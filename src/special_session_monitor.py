from allotment_update import excel_holdings
from Base import load_credentials
from allotment_fetch import fetch_allotment_holdings
from special_session_indicative_price_nse import get_ipo_indicative_price
import time
from datetime import datetime

CREDENTIALS_FILE = "credentials.json"

def special_session_monitor():
    print(
        "*************************************-----------special_session_monitor----------************************************")
    print(
        "##############################################################################################################")
    users = load_credentials(CREDENTIALS_FILE)

    while time_flag:
        for user in users:
            uci_user = user.get("uci")
            client_id = user.get("broker_client_id")
            password_user = user.get("password_broker")
            topt_broker = user.get("topt_broker")
            try:
                holdings = fetch_allotments(user_id=uci_user)
                #security_symbol, issue_price,exchange
            except Exception as e:
                print(e)
            try:
                indicative_price = get_ipo_indicative_price(symbol=security_symbol, exchange=exchange)
            except Exception as e:
                print(e)
            percent = 0
            if issue_price > indicative_price:
                percent = ((issue_price - indicative_price) / issue_price) * 100

            if category == "sme":
                if percent > 0:
                    sell_limit_lc(user_id=uci_user, symbol=security_symbol)
            elif category == "mb":
                if percent > 11.9:
                    sell_limit_lc(user_id=uci_user, symbol=security_symbol)
            else:
                print("No sold.")
        now = datetime.now()

        current_hour = now.hour
        current_minute = now.minute
        if current_hour == 9 and 0 <= current_minute <= 45:
            time_flag = True
        else:
            time_flag = False
            print("Time over for monitoring, exiting.")