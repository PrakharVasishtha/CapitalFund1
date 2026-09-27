import fund_kotak_get_balance
import asyncio
from fund_manager import ipo_required_fund
from fund_bank_to_kite import withdraw_bank_to_kite
from Base import load_credentials
from logger_setup import get_logger

logger = get_logger(__name__)

CREDENTIALS_FILE = "credentials.json"

def fund_trf_to_kite():
    logger.info("-----------fund_trf_to_kite: Checking excess balance to sweep to Kite----------")
    d0 = ipo_required_fund(0)
    d1 = ipo_required_fund(1)
    required_fund = d0 + d1
    logger.info(f"Required funds for upcoming IPOs: Day0={d0}, Day1={d1}, Total={required_fund}")

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

        if balance is None:
            balance = 0
        try:
            balance = int(float(balance))
        except (ValueError, TypeError):
            balance = 0

        logger.info(f"User {uci_user}: Kotak balance = ₹{balance}")
        if required_fund > balance:
            final_amount = 0
        else:
            final_amount = balance - required_fund

        logger.info(f"User {uci_user}: final_amount to sweep = ₹{final_amount}")
        if final_amount > 500:
            success, message = withdraw_bank_to_kite(
                user_uci=uci_user,
                broker_id=client_id,
                broker_password=password_user,
                totp_secret=topt_broker,
                bank_id=bank_user,
                bank_password=bank_password,
                EMAIL_USR=email_user,
                EMAIL_PSS=email_password,
                amount=final_amount,
            )
            logger.audit(f"AUDIT: Fund transfer to Kite | UCI: {uci_user} | Amount: {final_amount} | Success: {success} | Message: {message}")
        else:
            logger.info(f"User {uci_user}: No transfer required (amount ₹{final_amount} <= ₹500 threshold)")