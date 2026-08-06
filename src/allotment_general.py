from allotment_update import excel_holdings
from Base import *
from common_foundation import *
from allotment_fetch import fetch_allotment_holdings

CREDENTIALS_FILE = "credentials.json"


def ipo_allotment_manager():
    print(
        "*************************************-----------ipo_allotment_manager----------************************************")
    print(
        "##############################################################################################################")
    users = load_credentials(CREDENTIALS_FILE)
    for user in users:
        uci_user = user.get("uci")
        client_id = user.get("broker_client_id")
        password_user = user.get("password_broker")
        topt_broker = user.get("topt_broker")

        # NOTE: fetch_allotment_holdings() requires a security_symbol.
        # "NIFTYIETF" is used here as a placeholder to match the pattern
        # used elsewhere (trader_smws.py, trader_zerodha_sell.py). If you
        # actually want to check allotment holdings across multiple
        # symbols (NIFTYIETF / TATAGOLD / TATSILV), tell me and I'll loop
        # over all three instead of just one.
        holdings = 0
        try:
            holdings = fetch_allotment_holdings(
                user_id=client_id,
                password=password_user,
                totp_secret=topt_broker,
                security_symbol="NIFTYIETF",
            )
        except Exception as e:
            print(f"ipo_allotment_manager: fetch_allotment_holdings failed for {uci_user}: {e}")

        if holdings and holdings != 0:
            try:
                excel_holdings(uci_user)
            except Exception as e:
                print(f"ipo_allotment_manager: excel_holdings failed for {uci_user}: {e}")
        else:
            print("No allotment:", uci_user)