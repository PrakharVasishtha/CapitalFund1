import schedule
import foundation
import time
import os
import master_functions, application_ipo, fund_manager, smws, priority_ipo_smws_sell

# Functions setup
def ipo_entry():
    try:
        master_functions.latest_ipo_entry()
    except Exception as Argument:
        print("Problem in latest_ipo_entry")
        foundation.logger("system.txt",Argument,"ipo_entry")

def money_withdraw():
    try:
        fund_manager.daily_money_withdraw()
    except Exception as Argument:
        print("Problem in daily_money_withdraw")
        foundation.logger("system.txt",Argument,"money_withdraw")

def smws_seller():
    try:
        smws.smws_seller()
    except Exception as Argument:
        print("Problem in smws_seller")
        foundation.logger("system.txt",Argument,"smws_seller")

def smws_buyer():
    try:
        smws.smws_buyer()
    except Exception as Argument:
        print("Problem in smws_buyer")
        foundation.logger("system.txt",Argument,"smws_buyer")

def update_before_close():
    try:
        master_functions.update_3pm()
    except Exception as Argument:
        print("Problem in update_before_close")
        foundation.logger("system.txt",Argument,"update_before_close")

def ipo_application():
    try:
        application_ipo.ipo_application()
    except Exception as Argument:
        print("Problem in ipo_application")
        foundation.logger("system.txt",Argument,"ipo_application")

def run_now():
    try:
        print("running now")
        master_functions.latest_ipo_entry()
        fund_manager.daily_money_withdraw()
        smws.smws_seller()
        smws.smws_buyer()
        master_functions.update_3pm()
        application_ipo.ipo_application()
        print("Finished")

    except Exception as Argument:
        print("Problem in run_now",Argument)


#run_now()

# Task scheduling

schedule.every().day.at("08:30").do(ipo_entry)
#zerodha time instant money 9 to 4, upto 2 lakh
schedule.every().day.at("09:02").do(money_withdraw)
schedule.every().day.at("09:18").do(smws_seller)
schedule.every().day.at("09:25").do(smws_buyer)
schedule.every().day.at("10:05").do(update_before_close)
schedule.every().day.at("14:50").do(update_before_close)
schedule.every().day.at("14:55").do(ipo_application)


while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(1)