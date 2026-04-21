        # Schedule Library imported
import schedule
import time
#from master_functions import *
import os

from src import master_functions, IPO_application, fund_manager

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
        #fund_manager.daily_money_withdraw()
        master_functions.update_3pm()
        #IPO_application.ipo_application()
        print("Finished")

    except Exception as Argument:
        print("Problem in run_now")


#run_now()

# Task scheduling

schedule.every().day.at("08:45").do(ipo_entry)
schedule.every().day.at("10:05").do(update_before_close)
#schedule.every().day.at("10:10").do(money_withdraw)
schedule.every().day.at("14:50").do(update_before_close)
#schedule.every().day.at("14:55").do(ipo_application)


while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(1)