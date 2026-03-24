# Schedule Library imported
import schedule
import time
#from master_functions import *
import os

from src import master_functions

# Functions setup
def ipo_entry():
    try:
        master_functions.latest_ipo_entry()
    except Exception as Argument:
        print("Problem in latest_ipo_entry")

def update_before_close():
    try:
        master_functions.update_3pm()
    except Exception as Argument:
        print("Problem in update_before_close")

# Task scheduling
schedule.every().day.at("14:50").do(ipo_entry)
schedule.every().day.at("15:00").do(update_before_close)
schedule.every().day.at("15:10").do(update_before_close)
schedule.every().day.at("15:20").do(update_before_close)
schedule.every().day.at("15:30").do(update_before_close)
schedule.every().day.at("15:40").do(update_before_close)
schedule.every().day.at("15:50").do(update_before_close)


while True:
    # Checks whether a scheduled task
    # is pending to run or not
    schedule.run_pending()
    time.sleep(1)