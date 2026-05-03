import schedule
import time
import os

import master_functions, IPO_application, fund_manager, smws


# Functions setup
def ipo_entry():
    try:
        master_functions.latest_ipo_entry()
    except Exception as Argument:
        print("Problem in latest_ipo_entry")

def money_withdraw():
    try:
        fund_manager.daily_money_withdraw()
    except Exception as Argument:
        print("Problem in daily_money_withdraw")

def smws_seller():
    try:
        smws.smws_seller()
    except Exception as Argument:
        print("Problem in smws_seller")

def smws_buyer():
    try:
        smws.smws_buyer()
    except Exception as Argument:
        print("Problem in smws_buyer")

def update_before_close():
    try:
        master_functions.update_3pm()
    except Exception as Argument:
        print("Problem in update_before_close")

def ipo_application():
    try:
        IPO_application.ipo_application()
    except Exception as Argument:
        print("Problem in ipo_application")

def run_now():
    try:
        print("running now")
        master_functions.latest_ipo_entry()
        fund_manager.daily_money_withdraw()
        smws.smws_seller()
        smws.smws_buyer()
        master_functions.update_3pm()
        IPO_application.ipo_application()
        print("Finished")

    except Exception as Argument:
        print("Problem in run_now")


#run_now()

# Task scheduling

schedule.every().day.at("08:30").do(ipo_entry)
#zerodha time instant money 9 to 4, upto 2 lakh
schedule.every().day.at("09:02").do(money_withdraw)
schedule.every().day.at("09:18").do(smws_seller)
schedule.every().day.at("09:25").do(smws_buyer)
schedule.every().day.at("01:05").do(update_before_close)
schedule.every().day.at("14:50").do(update_before_close)
schedule.every().day.at("14:55").do(ipo_application)


while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(1)