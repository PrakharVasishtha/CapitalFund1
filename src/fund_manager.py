import pandas as pd
import openpyxl
from datetime import date, timedelta
import fund_kotak_get_balance
import time
import asyncio

from fund_zerodha_withdraw import withdraw_from_zerodha
from Base import get_last_row_sme, get_last_row_mb, get_excel_path, load_credentials, parse_float
from config import SME_IPO_FUND_RESERVE, MB_IPO_FUND_RESERVE
from logger_setup import get_logger

logger = get_logger(__name__)

CREDENTIALS_FILE = "credentials.json"


def strategy_status_10days():
    x = "Loading..."
    i = 0
    df = None
    while i < 3 and ("loading" in str(x).lower() or "nan" in str(x).lower()):
        url_csv = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv&t={int(time.time())}"
        try:
            df = pd.read_csv(url_csv)
            if len(df) > 23 and len(df.columns) > 4:
                x = str(df.iloc[23, 4]).strip()
        except Exception as e:
            logger.error(f"Error reading Google Sheet CSV: {e}")
        time.sleep(1)
        i = i + 1

    if df is None or "loading" in str(x).lower() or "nan" in str(x).lower():
        logger.warning("Strategy sheet not loaded with valid data, defaulting buy signal to 0")
        return 0

    try:
        b_nifty = parse_float(str(df.iloc[23, 4])) if len(df) > 23 else 0.0
        g_buy = parse_float(str(df.iloc[26, 4])) if len(df) > 26 else 0.0
        s_buy = parse_float(str(df.iloc[29, 4])) if len(df) > 29 else 0.0
        return int(b_nifty) + int(g_buy) + int(s_buy)
    except (ValueError, TypeError) as e:
        logger.exception(f"Invalid signal value in sheet: {e}")
        return 0

def ipo_required_fund(d = 0):
    row_sme = get_last_row_sme() - 1
    row_mb = get_last_row_mb() - 1
    total_sme_1 = 0
    total_sme_2 = 0
    total_mb_1 = 0
    total_mb_2 = 0

    path = get_excel_path()
    wb = openpyxl.load_workbook(path, data_only=True)
    sme_ws = wb['IPOSME']
    main_ws = wb['IPOMB']
    sme_fund = 0
    mb_fund = 0
    buy = int(strategy_status_10days())
    logger.info(f"IPO required fund check for day offset +{d} (strategy buy signal={buy})")
    target_date = date.today() + timedelta(days=d)
    target_day = target_date.day
    logger.info(f"Target closing day of month: {target_day}")
    for i in range(0, 9):
        rw = row_sme - i
        apply = sme_ws.cell(rw, 42).value
        close_date = sme_ws.cell(rw, 40).value

        if apply == 2 or apply == 3:
            if target_day == close_date:
                sme_fund = sme_fund + SME_IPO_FUND_RESERVE
                total_sme_1 = total_sme_1 + 1
                
        elif apply == 1:
            if target_day == close_date:
                if buy > 0:
                    sme_fund = sme_fund
                elif buy == 0:
                    sme_fund = sme_fund + SME_IPO_FUND_RESERVE
                    total_sme_2 = total_sme_2 + 1

    logger.info(f"SME fund required: ₹{sme_fund}")

    for i in range(0, 9):
        rw = row_mb - i
        apply = main_ws.cell(rw, 42).value
        close_date = main_ws.cell(rw, 40).value
        if apply == 2 or apply == 3:
            if target_day == close_date:
                mb_fund = mb_fund + MB_IPO_FUND_RESERVE
                total_mb_1 = total_mb_1 + 1
                
        elif apply == 1:
            if target_day == close_date:
                if buy > 0:
                    mb_fund = mb_fund
                elif buy == 0:
                    mb_fund = mb_fund + MB_IPO_FUND_RESERVE
                    total_mb_2 = total_mb_2 + 1

    logger.info(f"Mainboard fund required: ₹{mb_fund}")
    total_fund = sme_fund + mb_fund
    logger.info(f"Total Fund Required on Day {target_day} is: ₹{total_fund}")
    return total_fund


def daily_money_withdraw():
    logger.info("-----------daily_money_withdraw: Starting Daily Fund Assessment----------")
    d0 = ipo_required_fund(0)
    d1 = ipo_required_fund(1)
    required_fund = d0 + (0.9 * d1)
    logger.info(f"Fund requirements: Day0=₹{d0}, Day1=₹{d1}, Weighted Total Required=₹{required_fund}")
    if required_fund != 0:
        users = load_credentials(CREDENTIALS_FILE)
        for user in users:
            uci_user = user.get("uci")
            client_id = user.get("broker_client_id")
            password_user = user.get("password_broker")
            topt_broker = user.get("topt_broker")
            bank_user = user.get("bank_user")
            bank_password = user.get("bank_password")
            email_user = user.get("email_user")
            email_password = user.get("email_password")
            try:
                balance = asyncio.run(
                    fund_kotak_get_balance.get_kotak_balance(
                        USER_ID=bank_user,
                        PASSWORD=bank_password,
                        EMAIL_USR=email_user,
                        EMAIL_PSS=email_password
                    )
                )
            except Exception as e:
                logger.exception(f"Error getting Kotak balance for UCI {uci_user}: {e}")
                balance = 0
            final_amount = required_fund - balance
            logger.info(f"User {uci_user}: Kotak Balance=₹{balance}, Deficit to withdraw=₹{final_amount}")
            try:
                from common_foundation import send_telegram_notification
                send_telegram_notification(
                    f"💸 <b>Capital Withdrawal Initiated</b>\n"
                    f"<b>Account (UCI)</b>: {uci_user}\n"
                    f"<b>Required Amount</b>: ₹{final_amount:,.2f}"
                )
            except Exception:
                pass
            success, message = withdraw_from_zerodha(
                user_uci=uci_user,
                user_id=client_id,
                password=password_user,
                totp_secret=topt_broker,
                amount=final_amount,
                headless=True,
            )

            if success:
                logger.info(f"Withdrawal successful for UCI {uci_user}: {message}")
            else:
                logger.error(f"Withdrawal failed for UCI {uci_user}: {message}")
            
    else:
        logger.info("No withdrawal required today (required_fund is 0).")