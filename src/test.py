import pandas as pd
import openpyxl
from datetime import date,timedelta
import fund_kotak_get_balance
import time
import asyncio

from fund_zerodha_withdraw import withdraw_from_zerodha
from Base import get_last_row_sme, get_last_row_mb, get_excel_path, load_credentials

CREDENTIALS_FILE = "credentials.json"


def strategy_status_10days():
    #row_sme = get_last_row_sme() - 1

    x = "Loading..."
    i = 0
    while x == "Loading..." and i < 10:
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv"
        df = pd.read_csv(url_csv)
        time.sleep(2)
        x = df.iloc[23, 4]
        print(x)
        i = i + 1
    if i == 10:
        print("sheet not loading")
        
    buynifty = df.iloc[23, 4]
    print("buynifty:", buynifty)
    goldetfbuy = df.iloc[26, 4]
    print("goldetfbuy:", goldetfbuy)
    silveretfbuy = df.iloc[29, 4]
    print("silveretfbuy:", silveretfbuy)

strategy_status_10days()