"""
common_schedule_all.py
======================
Main entry point and daily scheduler for the CapitalFund1 automation system.

On startup, runs all tasks immediately via run_now(), then enters an infinite
loop scheduling each task at fixed times throughout the trading day.

Scheduled Tasks:
  08:00 - launch_streamlit_dashboard(): Initiate Streamlit control hub dashboard
  08:30 - ipo_entry()                : Scrape new IPOs into General.xlsx
  08:35 - update_dynamic_data()      : Refresh subscription, GMP, dynamic data
  08:40 - allotment_general()        : Check and record IPO allotments in allotted_holdings.xlsx
  09:00 - ss_start_lc_sell()         : Place LC sell orders for newly allotted shares today
  09:05 - money_withdraw()           : Withdraw funds from Zerodha to Kotak for IPOs
  09:10 - bank_to_kite()             : Transfer idle Kotak balance to Zerodha for SMWS
  09:15 - smws_seller()              : Sell SMWS ETFs per strategy signal
  09:20 - priority_ipo_sell_smws()   : Sell SMWS when IPO funds are required
  09:25 - smws_buyer()               : Buy SMWS ETFs per strategy signal
  09:32 - cancel_sale_order_if_loss(): Cancel pre-open LC sell orders if loss threshold exceeded
  10:01 - regular_session_ipo_sell() : Regular session IPO selling
  10:05 - listing_result()           : Check listing prices vs issue prices, update Pos/Neg column D
  12:05 - update_dynamic_data()      : Mid-day data refresh
  14:52 - update_dynamic_data()      : Pre-close data refresh
  14:55 - ipo_application()          : Apply to IPOs closing today via Kotak UPI

Usage:
  python src/common_schedule_all.py
"""
import schedule
from logger_setup import setup_logging
setup_logging()
import common_foundation
import time
import os
import sys
import subprocess
import socket
import threading
import database
import common_master_functions, allotment_application_ipo, fund_manager, trader_smws, trader_priority_ipo_smws_sell
import allotment_general as allotment_gen
import fund_transfer_for_smws
import ss_Before_session_close_cancel_sale_or_not
import ss_sale_order_on_lc_on_start_of_ss
import regular_session_sell
import ipo_listing_result

# ── Non-blocking Concurrency Controls ─────────────────────────────────────────
_running_jobs = set()
_job_lock = threading.Lock()


def run_threaded(job_func):
    """
    Execute a scheduled task in a background daemon thread.
    Prevents long-running network/scraping I/O from blocking the main scheduler
    event loop, ensuring critical listing-day tasks (09:00 LC Sell, 09:32 IEP check,
    10:01 Regular session) fire with second-level precision.
    Includes duplicate re-entrancy protection.
    """
    job_name = job_func.__name__
    with _job_lock:
        if job_name in _running_jobs:
            common_foundation.log_warning(
                f"Job '{job_name}' is already executing in background. Skipping duplicate run.",
                function_name="run_threaded"
            )
            return
        _running_jobs.add(job_name)

    def _worker():
        try:
            job_func()
        except Exception as e:
            common_foundation.log_error(
                f"Unhandled exception in background thread for '{job_name}': {e}",
                exc=e,
                function_name="run_threaded"
            )
        finally:
            with _job_lock:
                _running_jobs.discard(job_name)

    thread = threading.Thread(target=_worker, name=f"Thread-{job_name}", daemon=True)
    thread.start()


# ── Scheduled task wrappers ──────────────────────────────────────────────────
# Each function wraps the underlying logic with exception handling and logging.

def is_port_open(host="127.0.0.1", port=8501):
    """Check if a local TCP port is already open/in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def launch_streamlit_dashboard():
    """08:00 — Launch Streamlit control hub dashboard if not already running."""
    try:
        common_foundation.log_info("Checking Streamlit dashboard status...", "launch_streamlit_dashboard")
        if is_port_open(port=8501):
            common_foundation.log_info("Streamlit dashboard is already running on port 8501.", "launch_streamlit_dashboard")
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dashboard_path = os.path.join(base_dir, "dashboard.py")
        
        common_foundation.log_info(f"Initiating Streamlit dashboard from {dashboard_path}...", "launch_streamlit_dashboard")
        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]
        subprocess.Popen(cmd, cwd=base_dir)
        common_foundation.log_info("Streamlit dashboard initiated successfully.", "launch_streamlit_dashboard")
    except Exception as e:
        common_foundation.log_error(f"Problem initiating Streamlit dashboard: {e}", exc=e, function_name="launch_streamlit_dashboard")

def ipo_entry():
    """08:30 — Scrape latest IPOs from Chittorgarh and append to General.xlsx."""
    try:
        common_foundation.log_info("Executing IPO Entry task...", "ipo_entry")
        common_master_functions.latest_ipo_entry()
    except Exception as Argument:
        common_foundation.log_error("Problem in ipo_entry", exc=Argument, function_name="ipo_entry")

def allotment_general():
    """08:40 — Check Zerodha holdings for new IPO allotments and update allotted_holdings.xlsx."""
    try:
        common_foundation.log_info("Executing Allotment General task...", "allotment_general")
        allotment_gen.ipo_allotment_manager()
    except Exception as Argument:
        common_foundation.log_error("Problem in allotment_general", exc=Argument, function_name="allotment_general")

def ss_start_lc_sell():
    """09:00 — Place LC sell orders for newly allotted IPO shares today."""
    try:
        common_foundation.log_info("Executing SS Start LC Sell Order task...", "ss_start_lc_sell")
        ss_sale_order_on_lc_on_start_of_ss.place_lc_sell_orders_for_allotted_today()
    except Exception as Argument:
        common_foundation.log_error("Problem in ss_start_lc_sell", exc=Argument, function_name="ss_start_lc_sell")

def money_withdraw():
    """09:05 — Calculate IPO fund requirements and withdraw from Zerodha to Kotak bank."""
    try:
        common_foundation.log_info("Executing Money Withdraw task...", "money_withdraw")
        fund_manager.daily_money_withdraw()
    except Exception as Argument:
        common_foundation.log_error("Problem in money_withdraw", exc=Argument, function_name="money_withdraw")

def bank_to_kite():
    """09:10 — Transfer excess Kotak bank balance to Zerodha Kite for SMWS trading."""
    try:
        common_foundation.log_info("Executing Bank to Kite task...", "bank_to_kite")
        fund_transfer_for_smws.fund_trf_to_kite()
    except Exception as Argument:
        common_foundation.log_error("Problem in bank_to_kite", exc=Argument, function_name="bank_to_kite")

def smws_seller():
    """09:15 — Sell SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on strategy sheet signal."""
    try:
        common_foundation.log_info("Executing SMWS Sell task...", "smws_seller")
        trader_smws.smws_seller()
    except Exception as Argument:
        common_foundation.log_error("Problem in smws_seller", exc=Argument, function_name="smws_seller")

def priority_ipo_sell_smws():
    """09:20 — Sell SMWS ETFs with priority when IPO application funds are required."""
    try:
        common_foundation.log_info("Executing Priority IPO Sell SMWS task...", "priority_ipo_sell_smws")
        trader_priority_ipo_smws_sell.priority_ipo_sell_smws()
    except Exception as Argument:
        common_foundation.log_error("Problem in priority_ipo_sell_smws", exc=Argument, function_name="priority_ipo_sell_smws")

def smws_buyer():
    """09:25 — Buy SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on strategy sheet signal."""
    try:
        common_foundation.log_info("Executing SMWS Buy task...", "smws_buyer")
        trader_smws.smws_buyer()
    except Exception as Argument:
        common_foundation.log_error("Problem in smws_buyer", exc=Argument, function_name="smws_buyer")

def cancel_sale_order_if_loss():
    """09:32 — Cancel pre-open LC sell orders if IEP indicates discount/loss threshold exceeded."""
    try:
        common_foundation.log_info("Starting cancel_sale_order_if_loss task...", "cancel_sale_order_if_loss")
        ss_Before_session_close_cancel_sale_or_not.sale_order_cancel_or_not()
        common_foundation.log_info("Finished cancel_sale_order_if_loss task.", "cancel_sale_order_if_loss")
    except Exception as e:
        common_foundation.log_error(f"Error in cancel_sale_order_if_loss: {e}", exc=e, function_name="cancel_sale_order_if_loss")


def regular_session_ipo_sell():
    try:
        common_foundation.log_info("Starting regular_session_ipo_sell (10:00 AM) task...", "regular_session_ipo_sell")
        regular_session_sell.regular_session_ipo_sell()
        common_foundation.log_info("Finished regular_session_ipo_sell task.", "regular_session_ipo_sell")
    except Exception as e:
        common_foundation.log_error(f"Error in regular_session_ipo_sell: {e}", exc=e, function_name="regular_session_ipo_sell")


def listing_result():
    """10:05 — Check listing prices vs issue prices and update Pos/Neg in column D of General.xlsx."""
    try:
        common_foundation.log_info("Executing Listing Result task...", "listing_result")
        ipo_listing_result.update_listing_results()
        common_foundation.log_info("Finished Listing Result task.", "listing_result")
    except Exception as Argument:
        common_foundation.log_error("Problem in listing_result", exc=Argument, function_name="listing_result")


def update_dynamic_data():
    """12:05 / 14:52 — Refresh subscription, GMP, and dynamic_data_update data in General.xlsx."""
    try:
        common_foundation.log_info("Executing Update dynamic data task...", "update_dynamic_data")
        common_master_functions.dynamic_data_update()
    except Exception as Argument:
        common_foundation.log_error("Problem in update_dynamic_data", exc=Argument, function_name="update_dynamic_data")

def ipo_application():
    """14:55 — Submit UPI IPO applications via Kotak for IPOs closing today."""
    try:
        common_foundation.log_info("Executing IPO Application task...", "ipo_application")
        allotment_application_ipo.ipo_application()
    except Exception as Argument:
        common_foundation.log_error("Problem in ipo_application", exc=Argument, function_name="ipo_application")

def run_now():
    """
    Run initialization tasks immediately at startup before entering the scheduled loop.
    Initializes the Dual-Tier SQLite database and synchronizes with Excel workbooks.
    """
    try:
        common_foundation.log_info("Initializing Dual-Tier SQLite database & syncing Excel...", "run_now")
        try:
            database.init_db()
            database.import_all_from_excel()
        except Exception as db_err:
            common_foundation.log_error(f"Error initializing SQLite dual-tier engine: {db_err}", exc=db_err, function_name="run_now")

        try:
            import master_excel_manager
            master_excel_manager.sync_master_with_credentials()
        except Exception as me_err:
            common_foundation.log_error(f"Error syncing Master.xlsx: {me_err}", exc=me_err, function_name="run_now")
        
        launch_streamlit_dashboard()

    except Exception as Argument:
        common_foundation.log_error("Problem in run_now", exc=Argument, function_name="run_now")


# Setup Daily Schedule (Using run_threaded to prevent blocking the main scheduler event loop)
schedule.every().day.at("08:00").do(run_threaded, launch_streamlit_dashboard)
schedule.every().day.at("08:30").do(run_threaded, ipo_entry)
schedule.every().day.at("08:35").do(run_threaded, update_dynamic_data)
schedule.every().day.at("08:40").do(run_threaded, allotment_general)
schedule.every().day.at("09:00").do(run_threaded, ss_start_lc_sell)
schedule.every().day.at("09:05").do(run_threaded, money_withdraw)
schedule.every().day.at("09:10").do(run_threaded, bank_to_kite)
schedule.every().day.at("09:15").do(run_threaded, smws_seller)
schedule.every().day.at("09:20").do(run_threaded, priority_ipo_sell_smws)
schedule.every().day.at("09:25").do(run_threaded, smws_buyer)
schedule.every().day.at("09:32").do(run_threaded, cancel_sale_order_if_loss)
schedule.every().day.at("10:01").do(run_threaded, regular_session_ipo_sell)
schedule.every().day.at("10:05").do(run_threaded, listing_result)
schedule.every().day.at("12:05").do(run_threaded, update_dynamic_data)
schedule.every().day.at("14:52").do(run_threaded, update_dynamic_data)
schedule.every().day.at("14:55").do(run_threaded, ipo_application)

if __name__ == "__main__":
    try:
        run_now()
        common_foundation.log_info("Scheduler loop started (tick interval: 1s, non-blocking threaded execution active).", "__main__")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        common_foundation.log_info("Scheduler stopped by user (KeyboardInterrupt).", "__main__")