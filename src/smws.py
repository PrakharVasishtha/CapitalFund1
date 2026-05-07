from Base import load_credentials
from zerodha_base import get_balance_zerodha
from zerodha_buy import zerodha_buy
import pandas as pd
import openpyxl
from datetime import date,timedelta
import time
import asyncio

from zerodha_sell import zerodha_sell

CREDENTIALS_FILE = "credentials.json"

def smws_buyer():
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv"
    df0 = pd.read_csv(url_csv)
    time.sleep(1)
    df = pd.read_csv(url_csv)
    buynifty = df.iloc[23, 3]
    print("buynifty:", buynifty)
    goldetfbuy = df.iloc[26, 3]
    print("goldetfbuy:", goldetfbuy)
    silveretfbuy = df.iloc[29, 3]
    print("silveretfbuy:", silveretfbuy)
    buynifty =1
    total_securities = int(buynifty)+int(goldetfbuy)+int(silveretfbuy)

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
            if amount_per_security > 3000:
                if int(buynifty) == 1:
                    zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=amount_per_security,security_symbol="NIFTYIETF")
                if int(goldetfbuy) == 1:
                    zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=amount_per_security,security_symbol="TATAGOLD")
                if int(silveretfbuy) == 1:
                    zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=amount_per_security,security_symbol="TATSILV")

def smws_seller():
    print("---------smws_seller--------")
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv"
    df0 = pd.read_csv(url_csv)
    time.sleep(1)
    df = pd.read_csv(url_csv)
    sellnifty = df.iloc[24, 3]
    print("sellnifty:", sellnifty)
    goldetfsell = df.iloc[27, 3]
    print("goldetfsell:", goldetfsell)
    silveretfsell = df.iloc[30, 3]
    print("silveretfsell:", silveretfsell)
    buynifty =1
    total_securities = int(sellnifty)+int(goldetfsell)+int(silveretfsell)

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


#smws_buyer()
smws_seller()