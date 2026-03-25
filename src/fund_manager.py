import pandas as pd
import Base
import openpyxl
from datetime import date
import time

from zerodha_withdraw import withdraw_from_zerodha
from trading_base import *

CREDENTIALS_FILE = "credentials.json"


def strategy_status_10days():
    row_sme = Base.get_last_row_sme() - 1

    url_csv= "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv"
    df = pd.read_csv(url_csv)
    buy = df.iloc[23, 2]
    print("buy:", buy)
    return buy

def ipo_required_fund():
    row_sme = Base.get_last_row_sme() - 1
    row_mb = Base.get_last_row_mb() - 1
    total_sme_1 = 0
    total_sme_2 = 0
    total_mb_1 = 0
    total_mb_2 = 0

    path = '../General.xlsx'
    wb = openpyxl.load_workbook(path, data_only=True)
    sme_ws = wb['IPOSME']
    main_ws = wb['IPOMB']
    sme_fund = 0
    mb_fund = 0
    buy=int(strategy_status_10days())
    print(type(buy))
    for i in range(0, 9):
        rw = row_sme - i
        apply = sme_ws.cell(rw, 42).value
        #print(apply)
        close_date = sme_ws.cell(rw, 40).value
        today = date.today().day
        if apply == 2 or apply == 3:
            
            if today == close_date:
                #print("today is IPO at row:", rw)
                sme_fund = sme_fund + 280000
                total_sme_1 = total_sme_1 + 1
                
        elif apply == 1:
            if today == close_date:
                if buy == 3 or buy == 4:
                    sme_fund = sme_fund
                elif buy == 0 or buy == 1 or buy == 2:
                    sme_fund = sme_fund + 280000
                    total_sme_2 = total_sme_2 + 1
                
                
    print("sme fund",sme_fund)
    print("total_sme_1:", total_sme_1)
    print("total_sme_2:", total_sme_2)

    for i in range(0, 9):
        rw = row_mb - i
        apply = main_ws.cell(rw, 42).value
        #print(apply)
        close_date = main_ws.cell(rw, 40).value
        today = date.today().day
        if apply == 2 or apply == 3:
            if today == close_date:
                mb_fund = mb_fund + 209000
                total_mb_1 = total_mb_1 + 1
                
        elif apply == 1:
            if today == close_date:
                if buy == 3 or buy == 4:
                    mb_fund = mb_fund
                elif buy == 0 or buy == 1 or buy == 2:
                    mb_fund = mb_fund + 209000
                    total_mb_2 = total_mb_2 + 1


    print("mb fund", mb_fund)
    print("total_mb_1:", total_mb_1)
    print("total_mb_2:", total_mb_2)
    total_fund=sme_fund + mb_fund
    print("Total Fund Required Today:",total_fund)
    return total_fund


def daily_money_withdraw():
    required_fund = ipo_required_fund()
    if required_fund != 0:
        users = load_credentials(CREDENTIALS_FILE)
        #Users
        for user in users:
            client_id = user.get("broker_client_id")
            password_user = user.get("password")
            topt_broker = user.get("topt_broker")


            success, message = withdraw_from_zerodha(
                user_id=client_id,
                password=password_user,
                totp_secret=topt_broker,
                amount=required_fund,
                headless=False,
            )

            print(success, message)
    else:
        print("No withdrawal required.")

#print(strategy_status_10days())
#print("ipo_required_fund",ipo_required_fund())
#print(daily_money_withdraw())