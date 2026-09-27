from Base import load_credentials
from fund_manager import ipo_required_fund
from trader_zerodha_sell import zerodha_sell
from config import MIN_ETF_ORDER_AMOUNT, SMWS_DEFAULT_SECURITIES
from logger_setup import get_logger

logger = get_logger(__name__)

CREDENTIALS_FILE = "credentials.json"

def priority_ipo_sell_smws():
    logger.info("priority_ipo_sell_smws: Evaluating priority liquidation for IPO funds")
    required_fund_today = ipo_required_fund(0)
    required_fund_tomorrow = ipo_required_fund(1)
    if required_fund_tomorrow != 0:
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
                balance = 120000
                #balance = asyncio.run(kotak_get_balance.get_kotak_balance(USER_ID=bank_user, PASSWORD=bank_password, EMAIL_USR=email_user,EMAIL_PSS=email_password))
            except Exception as e:
                logger.exception(f"Error getting Kotak balance: {e}")
                balance = 0
            carryover_bank_balance = balance - required_fund_today
            if carryover_bank_balance < 0:
                carryover_bank_balance = 0
            logger.info(f"carryover_bank_balance: {carryover_bank_balance}")
            money_need_tomorrow = required_fund_tomorrow - carryover_bank_balance
            logger.info(f"User {client_id}: money needed tomorrow = {money_need_tomorrow}")
            if money_need_tomorrow > MIN_ETF_ORDER_AMOUNT:
                for symbol in SMWS_DEFAULT_SECURITIES:
                    try:
                        zerodha_sell(user_id=client_id, password=password_user, totp_secret=topt_broker, security_symbol=symbol)
                    except Exception as e:
                        logger.exception(f"Error selling {symbol} for {client_id}: {e}")
        return 1
    else:
        logger.info("No priority ETF liquidation required (required_fund_tomorrow is 0)")
        return 0

#print(priority_ipo_sell_smws())