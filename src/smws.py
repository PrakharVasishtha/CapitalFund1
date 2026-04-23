from src.Base import load_credentials
from src.zerodha_buy import zerodha_buy
import pandas as pd
import openpyxl
from datetime import date,timedelta
import time
import asyncio

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
    if int(buynifty)+int(goldetfbuy)+int(silveretfbuy)>0:
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
            buy_amount = 90

            if int(buynifty) == 1:
                zerodha_buy(user_id=client_id,password=password_user,totp_secret=topt_broker,amount=buy_amount,security_symbol="NIFTYIETF")


smws_buyer()