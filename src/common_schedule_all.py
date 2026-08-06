import schedule
import common_foundation
import time
import os
import common_master_functions, allotment_application_ipo, fund_manager, trader_smws, trader_priority_ipo_smws_sell
import fund_transfer_for_smws


# Functions setup
def ipo_entry():
    try:
        print("IPO Entry")
        common_master_functions.latest_ipo_entry()
    except Exception as Argument:
        print("Problem in latest_ipo_entry")
        common_foundation.logger("system.txt",Argument,"ipo_entry")

def money_withdraw():
    try:
        print("Money Withdraw")
        fund_manager.daily_money_withdraw()
    except Exception as Argument:
        print("Problem in daily_money_withdraw")
        common_foundation.logger("system.txt",Argument,"money_withdraw")

def bank_to_kite():
    try:
        print("Bank to Kite")
        fund_transfer_for_smws.fund_trf_to_kite()
    except Exception as Argument:
        print("Problem in bank_to_kite")
        common_foundation.logger("system.txt",Argument,"bank_to_kite")

def smws_seller():
    try:
        print("SMWS Sell")
        trader_smws.smws_seller()
    except Exception as Argument:
        print("Problem in smws_seller")
        common_foundation.logger("system.txt",Argument,"smws_seller")

def priority_ipo_sell_smws():
    try:
        print("Priority IPO Sell SMWS")
        trader_priority_ipo_smws_sell.priority_ipo_sell_smws()
    except Exception as Argument:
        print("Problem in priority_ipo_sell_smws")
        common_foundation.logger("system.txt",Argument,"priority_ipo_sell_smws")

def smws_buyer():
    try:
        print("SMWS Buy")
        trader_smws.smws_buyer()
    except Exception as Argument:
        print("Problem in smws_buyer")
        common_foundation.logger("system.txt",Argument,"smws_buyer")

def update_before_close():
    try:
        print("Update Before Close")
        common_master_functions.update_3pm()
    except Exception as Argument:
        print("Problem in update_before_close")
        common_foundation.logger("system.txt",Argument,"update_before_close")

def ipo_application():
    try:
        print("IPO Application")
        allotment_application_ipo.ipo_application()
    except Exception as Argument:
        print("Problem in ipo_application")
        common_foundation.logger("system.txt",Argument,"ipo_application")

def run_now():
    try:
        print("running now")
        #common_master_functions.latest_ipo_entry()
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

run_now()
schedule.every().day.at("08:30").do(ipo_entry)
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