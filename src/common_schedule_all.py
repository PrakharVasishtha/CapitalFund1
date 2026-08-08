"""
common_schedule_all.py
======================
Main entry point and daily scheduler for the CapitalFund1 automation system.

On startup, runs all tasks immediately via run_now(), then enters an infinite
loop scheduling each task at fixed times throughout the trading day.

Scheduled Tasks:
  08:30 - ipo_entry()           : Scrape new IPOs into General.xlsx
  08:35 - allotment_general()   : Check and record IPO allotments in allotted_holdings.xlsx
  09:02 - money_withdraw()      : Withdraw funds from Zerodha to Kotak for IPOs
  09:09 - bank_to_kite()        : Transfer idle Kotak balance to Zerodha for SMWS
  09:18 - smws_seller()         : Sell SMWS ETFs per strategy signal
  09:18 - priority_ipo_sell_smws(): Sell SMWS when IPO funds are needed
  09:25 - smws_buyer()          : Buy SMWS ETFs per strategy signal
  10:05 - update_before_close() : Refresh IPO data in General.xlsx
  14:50 - update_before_close() : Pre-close data refresh
  14:55 - ipo_application()     : Apply to IPOs closing today
  15:05 - update_before_close() : Final post-close update

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


# ── Scheduled task wrappers ──────────────────────────────────────────────────
# Each function wraps the underlying logic with exception handling and logging.

def ipo_entry():
    """08:30 — Scrape latest IPOs from Chittorgarh and append to General.xlsx."""
    try:
        print("IPO Entry")
        common_master_functions.latest_ipo_entry()
    except Exception as Argument:
        print("Problem in latest_ipo_entry")
        common_foundation.logger("system.txt",Argument,"ipo_entry")

def allotment_general():
    """08:35 — Check Zerodha holdings for new IPO allotments and update allotted_holdings.xlsx."""
    try:
        print("Allotment General")
        allotment_gen.ipo_allotment_manager()
    except Exception as Argument:
        print("Problem in allotment_general")
        common_foundation.logger("system.txt", Argument, "allotment_general")

def money_withdraw():
    """09:02 — Calculate IPO fund requirements and withdraw from Zerodha to Kotak bank."""
    try:
        print("Money Withdraw")
        fund_manager.daily_money_withdraw()
    except Exception as Argument:
        print("Problem in daily_money_withdraw")
        common_foundation.logger("system.txt",Argument,"money_withdraw")

def bank_to_kite():
    """09:09 — Transfer excess Kotak bank balance to Zerodha Kite for SMWS trading."""
    try:
        print("Bank to Kite")
        fund_transfer_for_smws.fund_trf_to_kite()
    except Exception as Argument:
        print("Problem in bank_to_kite")
        common_foundation.logger("system.txt",Argument,"bank_to_kite")

def smws_seller():
    """09:18 — Sell SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on strategy sheet signal."""
    try:
        print("SMWS Sell")
        trader_smws.smws_seller()
    except Exception as Argument:
        print("Problem in smws_seller")
        common_foundation.logger("system.txt",Argument,"smws_seller")

def priority_ipo_sell_smws():
    """09:18 — Sell SMWS ETFs with priority when IPO application funds are required."""
    try:
        print("Priority IPO Sell SMWS")
        trader_priority_ipo_smws_sell.priority_ipo_sell_smws()
    except Exception as Argument:
        print("Problem in priority_ipo_sell_smws")
        common_foundation.logger("system.txt",Argument,"priority_ipo_sell_smws")

def smws_buyer():
    """09:25 — Buy SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on strategy sheet signal."""
    try:
        print("SMWS Buy")
        trader_smws.smws_buyer()
    except Exception as Argument:
        print("Problem in smws_buyer")
        common_foundation.logger("system.txt",Argument,"smws_buyer")

def update_before_close():
    """10:05 / 14:50 / 15:05 — Refresh subscription, GMP, and 3pm data in General.xlsx."""
    try:
        print("Update Before Close")
        common_master_functions.update_3pm()
    except Exception as Argument:
        print("Problem in update_before_close")
        common_foundation.logger("system.txt",Argument,"update_before_close")

def ipo_application():
    """14:55 — Submit UPI IPO applications via Kotak for IPOs closing today."""
    try:
        print("IPO Application")
        allotment_application_ipo.ipo_application()
    except Exception as Argument:
        print("Problem in ipo_application")
        common_foundation.logger("system.txt",Argument,"ipo_application")

def run_now():
    """
    Run all tasks immediately in sequence.
    Called once at startup before the scheduled loop begins.
    Useful for catching up on any tasks missed if the script was restarted mid-day.
    """
    try:
        print("running now")
        common_master_functions.latest_ipo_entry()
        allotment_gen.ipo_allotment_manager()
        fund_manager.daily_money_withdraw()
        fund_transfer_for_smws.fund_trf_to_kite()
        trader_smws.smws_seller()
        trader_priority_ipo_smws_sell.priority_ipo_sell_smws()
        trader_smws.smws_buyer()
        common_master_functions.update_3pm()
        allotment_application_ipo.ipo_application()
        print("Finished")

    except Exception as Argument:
        print("Problem in run_now",Argument)
        common_foundation.logger("system.txt", Argument, "run_now")

#run_now()
schedule.every().day.at("08:30").do(ipo_entry)
schedule.every().day.at("08:40").do(allotment_general)
schedule.every().day.at("09:02").do(money_withdraw)
schedule.every().day.at("09:09").do(bank_to_kite)
schedule.every().day.at("09:18").do(smws_seller)
schedule.every().day.at("09:18").do(priority_ipo_sell_smws)
schedule.every().day.at("09:25").do(smws_buyer)
schedule.every().day.at("10:05").do(update_before_close)
schedule.every().day.at("14:50").do(update_before_close)
schedule.every().day.at("14:55").do(ipo_application)
schedule.every().day.at("15:05").do(update_before_close)

while True:
    schedule.run_pending()
    time.sleep(1)