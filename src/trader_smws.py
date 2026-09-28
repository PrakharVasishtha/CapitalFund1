from Base import load_credentials, parse_float
from trader_zerodha_base import get_balance_zerodha
from trader_zerodha_buy import zerodha_buy
from trader_zerodha_sell import zerodha_sell
from logger_setup import get_logger
import pandas as pd
import openpyxl
from datetime import date, timedelta
import time
import asyncio

logger = get_logger(__name__)

CREDENTIALS_FILE = "credentials.json"

def smws_buyer():
    logger.info("-----------smws_buyer: Starting ETF Buy Evaluation----------")

    # Warm the Google Sheet to force GOOGLEFINANCE/IMPORTRANGE recalculation
    try:
        from smws_sheet_warmer import recalculate_smws_sheet
        result = recalculate_smws_sheet(force=True)
        logger.info(f"Sheet warmer result: {result.get('status')} ({result.get('duration', '?')}s)")
        if result.get("status") == "success":
            time.sleep(5)   # Allow Google backend to propagate recalculated values
    except Exception as _e:
        logger.warning(f"Sheet warmer unavailable (non-fatal): {_e}")

    x = "Loading..."
    i = 0
    df = None
    while i < 3 and ("loading" in str(x).lower() or "nan" in str(x).lower()):
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv"
        try:
            df = pd.read_csv(url_csv)
            if len(df) > 23 and len(df.columns) > 4:
                x = df.iloc[23, 4]
        except Exception as e:
            logger.error(f"Error reading Google Sheet CSV: {e}")
        time.sleep(2)
        i = i + 1

    if df is None or "loading" in str(x).lower() or "nan" in str(x).lower():
        logger.warning("Strategy sheet not loaded with valid data")
        return False

    try:
        buynifty = int(parse_float(str(df.iloc[23, 4]))) if len(df) > 23 and len(df.columns) > 4 else 0
        goldetfbuy = int(parse_float(str(df.iloc[26, 4]))) if len(df) > 26 and len(df.columns) > 4 else 0
        silveretfbuy = int(parse_float(str(df.iloc[29, 4]))) if len(df) > 29 and len(df.columns) > 4 else 0
        logger.info(f"SMWS Buy Signals: NIFTYIETF={buynifty}, TATAGOLD={goldetfbuy}, TATSILV={silveretfbuy}")
        total_securities = buynifty + goldetfbuy + silveretfbuy
    except (ValueError, TypeError) as e:
        logger.exception(f"Invalid strategy signal value in sheet: {e}")
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
            amount_per_security = int(buy_amount / total_securities)
            logger.info(f"User {client_id}: Balance={buy_amount}, Amount per security={amount_per_security}")
            if amount_per_security > 2000:
                try:
                    if buynifty == 1:
                        zerodha_buy(user_id=client_id, password=password_user, totp_secret=topt_broker, amount=amount_per_security, security_symbol="NIFTYIETF")
                except Exception as e:
                    logger.exception(f"Error buying NIFTYIETF for {client_id}: {e}")
                try:
                    if goldetfbuy == 1:
                        zerodha_buy(user_id=client_id, password=password_user, totp_secret=topt_broker, amount=amount_per_security, security_symbol="TATAGOLD")
                except Exception as e:
                    logger.exception(f"Error buying TATAGOLD for {client_id}: {e}")
                try:
                    if silveretfbuy == 1:
                        zerodha_buy(user_id=client_id, password=password_user, totp_secret=topt_broker, amount=amount_per_security, security_symbol="TATSILV")
                except Exception as e:
                    logger.exception(f"Error buying TATSILV for {client_id}: {e}")
    else:
        logger.info("Total securities SMWS buy signal is 0, not buying any securities")

def smws_seller():
    logger.info("-----------smws_seller: Starting ETF Sell Evaluation----------")

    # Warm the Google Sheet to force GOOGLEFINANCE/IMPORTRANGE recalculation
    try:
        from smws_sheet_warmer import recalculate_smws_sheet
        result = recalculate_smws_sheet(force=True)
        logger.info(f"Sheet warmer result: {result.get('status')} ({result.get('duration', '?')}s)")
        if result.get("status") == "success":
            time.sleep(5)   # Allow Google backend to propagate recalculated values
    except Exception as _e:
        logger.warning(f"Sheet warmer unavailable (non-fatal): {_e}")

    x = "Loading..."
    i = 0
    df = None
    while i < 3 and ("loading" in str(x).lower() or "nan" in str(x).lower()):
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?gid=614695683&single=true&output=csv"
        try:
            df = pd.read_csv(url_csv)
            if len(df) > 24 and len(df.columns) > 4:
                x = df.iloc[24, 4]
        except Exception as e:
            logger.error(f"Error reading Google Sheet CSV: {e}")
        time.sleep(2)
        i = i + 1

    if df is None or "loading" in str(x).lower() or "nan" in str(x).lower():
        logger.warning("Strategy sheet not loaded with valid data")
        return False

    try:
        sellnifty = int(parse_float(str(df.iloc[24, 3]))) if len(df) > 24 and len(df.columns) > 3 else 0
        goldetfsell = int(parse_float(str(df.iloc[27, 3]))) if len(df) > 27 and len(df.columns) > 3 else 0
        silveretfsell = int(parse_float(str(df.iloc[30, 3]))) if len(df) > 30 and len(df.columns) > 3 else 0
        logger.info(f"SMWS Sell Signals: NIFTYIETF={sellnifty}, TATAGOLD={goldetfsell}, TATSILV={silveretfsell}")
        total_securities = sellnifty + goldetfsell + silveretfsell
    except (ValueError, TypeError) as e:
        logger.exception(f"Invalid strategy signal value in sheet: {e}")
        return False

    if total_securities > 0:
        users = load_credentials(CREDENTIALS_FILE)
        for user in users:
            client_id = user.get("broker_client_id")
            password_user = user.get("password_broker")
            topt_broker = user.get("topt_broker")
            bank_user = user.get("bank_user")
            bank_password = user.get("bank_password")
            email_user = user.get("email_user")
            email_password = user.get("email_password")

            try:
                if sellnifty == 1:
                    zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker, security_symbol="NIFTYIETF")
            except Exception as e:
                logger.exception(f"Error selling NIFTYIETF for {client_id}: {e}")
            try:
                if goldetfsell == 1:
                    zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker, security_symbol="TATAGOLD")
            except Exception as e:
                logger.exception(f"Error selling TATAGOLD for {client_id}: {e}")
            try:
                if silveretfsell == 1:
                    zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker, security_symbol="TATSILV")
            except Exception as e:
                logger.exception(f"Error selling TATSILV for {client_id}: {e}")
    else:
        logger.info("Total securities SMWS sell signal is 0, not selling any securities") 

#smws_buyer()
#smws_seller()
#