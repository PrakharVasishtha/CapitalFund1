"""
common_schedule_all.py
======================
Main entry point and daily scheduler for the CapitalFund1 automation system.

On startup, runs all tasks immediately via run_now(), then enters an infinite
loop scheduling each task at fixed times throughout the trading day.

Scheduled Tasks:
  08:30 - ipo_entry()                : Scrape new IPOs into General.xlsx
  08:40 - allotment_general()        : Check and record IPO allotments in allotted_holdings.xlsx
  09:00 - ss_start_lc_sell()         : Place LC sell orders for newly allotted shares today
  09:02 - money_withdraw()           : Withdraw funds from Zerodha to Kotak for IPOs
  09:09 - bank_to_kite()             : Transfer idle Kotak balance to Zerodha for SMWS
  09:18 - smws_seller()              : Sell SMWS ETFs per strategy signal
  09:18 - priority_ipo_sell_smws()   : Sell SMWS when IPO funds are needed
  09:25 - smws_buyer()               : Buy SMWS ETFs per strategy signal
  09:32 - cancel_sale_order_if_loss(): Cancel pre-open LC sell orders if loss threshold exceeded
  10:05 - update_before_close()      : Refresh IPO data in General.xlsx
  14:50 - update_before_close()      : Pre-close 3pm data refresh
  14:55 - ipo_application()          : Apply to IPOs closing today via Kotak UPI
  15:05 - update_before_close()      : Final post-close update

Usage:
  python src/common_schedule_all.py
"""
import schedule
import common_foundation
import time
import os
import common_master_functions, allotment_application_ipo, fund_manager, trader_smws, trader_priority_ipo_smws_sell
import allotment_general as allotment_gen
import fund_transfer_for_smws
import ss_Before_session_close_cancel_sale_or_not
import ss_sale_order_on_lc_on_start_of_ss
import regular_session_sell


# ── Scheduled task wrappers ──────────────────────────────────────────────────
# Each function wraps the underlying logic with exception handling and logging.

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
    Run all tasks immediately in sequence.
    Called once at startup before the scheduled loop begins.
    Useful for catching up on any tasks missed if the script was restarted mid-day.
    """
    try:
        common_foundation.log_info("Running all tasks now in sequence...", "run_now")
        try:
            import master_excel_manager
            master_excel_manager.sync_master_with_credentials()
        except Exception as me_err:
            common_foundation.log_error(f"Error syncing Master.xlsx: {me_err}", exc=me_err, function_name="run_now")
        #ipo_entry()
        #allotment_general()
        #ss_start_lc_sell()
        #money_withdraw()
        #bank_to_kite()
        #smws_seller()
        #priority_ipo_sell_smws()
        #smws_buyer()
        #cancel_sale_order_if_loss()
        #update_dynamic_data()
        #regular_session_ipo_sell()
        #ipo_application()
        #common_foundation.log_info("Finished running all tasks.", "run_now")

    except Exception as Argument:
        common_foundation.log_error("Problem in run_now", exc=Argument, function_name="run_now")

# Setup Daily Schedule
schedule.every().day.at("08:30").do(ipo_entry)
schedule.every().day.at("08:35").do(update_dynamic_data)
schedule.every().day.at("08:40").do(allotment_general)
schedule.every().day.at("09:00").do(ss_start_lc_sell)
schedule.every().day.at("09:05").do(money_withdraw)
schedule.every().day.at("09:10").do(bank_to_kite)
schedule.every().day.at("09:15").do(smws_seller)
schedule.every().day.at("09:20").do(priority_ipo_sell_smws)
schedule.every().day.at("09:25").do(smws_buyer)
schedule.every().day.at("09:32").do(cancel_sale_order_if_loss)
schedule.every().day.at("10:01").do(regular_session_ipo_sell)
schedule.every().day.at("12:05").do(update_dynamic_data)
schedule.every().day.at("14:52").do(update_dynamic_data)
schedule.every().day.at("14:55").do(ipo_application)

if __name__ == "__main__":
    try:
        run_now()
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        common_foundation.log_info("Scheduler stopped by user (KeyboardInterrupt).", "__main__")