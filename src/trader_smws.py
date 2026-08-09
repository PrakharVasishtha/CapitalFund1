from Base import load_credentials
from trader_zerodha_base import get_balance_zerodha
from trader_zerodha_buy import zerodha_buy
import pandas as pd
import openpyxl
from datetime import date,timedelta
import time
import asyncio

from trader_zerodha_sell import zerodha_sell

CREDENTIALS_FILE = "credentials.json"

def smws_buyer():
    print("-----------smws_buyer----------")

    x = "Loading..."
    i = 0
    df = None
    while ("Loading" in x or "nan" in x) and i < 10:
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?gid=614695683&single=true&output=csv"
        try:
            df = pd.read_csv(url_csv)
            time.sleep(6)
            x = df.iloc[23, 4]
        except Exception as e:
            print("Error reading Google Sheet CSV:", e)
        time.sleep(2)
        i = i + 1
        print(i)
    if i == 10 or x == "Loading..." or df is None:
        print("sheet not loading")
        return False

    try:
        buynifty = df.iloc[23, 4]
        print("buynifty:", buynifty)
        goldetfbuy = df.iloc[26, 4]
        print("goldetfbuy:", goldetfbuy)
        silveretfbuy = df.iloc[29, 4]
        print("silveretfbuy:", silveretfbuy)
        total_securities = int(buynifty)+int(goldetfbuy)+int(silveretfbuy)
    except (ValueError, TypeError) as e:
        print("Invalid strategy signal value in sheet:", e)
        return False

    if total_securities > 0:
        users = load_credentials(CREDENTIALS_FILE)
        # Users
        for user in users:
            client_id = user.get("broker_client_id")
            password_user = user.get("password_broker")
            topt_broker = user.get("topt_broker")
            bank_user = user.get("bank_user")
            bank_password = user.get("bank_password")
            email_user = user.get("email_user")
            email_password = user.get("email_password")
            buy_amount = get_balance_zerodha(user_id=client_id,password=password_user,totp_secret=topt_broker)
            buy_amount = int(buy_amount/3)
            amount_per_security = int(buy_amount/ total_securities)
            print("amount_per_security:", amount_per_security)
            if amount_per_security > 2000:
                try:
                    if int(buynifty) == 1:
                        zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=amount_per_security,security_symbol="NIFTYIETF")
                except Exception as e:
                    print(e)
                try:
                    if int(goldetfbuy) == 1:
                        zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=amount_per_security,security_symbol="TATAGOLD")
                except Exception as e:
                    print(e)
                try:
                    if int(silveretfbuy) == 1:
                        zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=amount_per_security,security_symbol="TATSILV")
                except Exception as e:
                    print(e)
    else:
        print("Total securities SMWS is 0, not buying any securities")

def smws_seller():
    print(
        "-----------smws_seller----------")
    x = "Loading..."
    i = 0
    df = None
    while ("Loading" in x or "nan" in x) and i < 10:
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?gid=614695683&single=true&output=csv"
        try:
            df = pd.read_csv(url_csv)
            time.sleep(6)
            x = df.iloc[24, 4]
        except Exception as e:
            print("Error reading Google Sheet CSV:", e)
        time.sleep(2)
        i = i + 1
        print(i)
    if i == 10 or x == "Loading..." or df is None:
        print("sheet not loading")
        return False

    try:
        sellnifty = df.iloc[24, 3]
        print("sellnifty:", sellnifty)
        goldetfsell = df.iloc[27, 3]
        print("goldetfsell:", goldetfsell)
        silveretfsell = df.iloc[30, 3]
        print("silveretfsell:", silveretfsell)
        sellnifty = 1
        total_securities = int(sellnifty)+int(goldetfsell)+int(silveretfsell)
    except (ValueError, TypeError) as e:
        print("Invalid strategy signal value in sheet:", e)
        return False

    if total_securities > 0:
        users = load_credentials(CREDENTIALS_FILE)
        # Users
        for user in users:
            client_id = user.get("broker_client_id")
            password_user = user.get("password_broker")
            topt_broker = user.get("topt_broker")
            bank_user = user.get("bank_user")
            bank_password = user.get("bank_password")
            email_user = user.get("email_user")
            email_password = user.get("email_password")

            #sellnifty = 1
            #goldetfsell = 0
            #silveretfsell = 0
            try:
                if int(sellnifty) == 1:
                    zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker,
                                 security_symbol="NIFTYIETF")
            except Exception as e:
                print(e)
            try:
                if int(goldetfsell) == 1:
                    zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker,
                                 security_symbol="TATAGOLD")
            except Exception as e:
                print(e)
            try:
                if int(silveretfsell) == 1:
                    zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker,
                                 security_symbol="TATSILV")
            except Exception as e:
                print(e)
    else:
        print("Total securities SMWS is 0, not selling any securities") 

#smws_buyer()
#smws_seller()