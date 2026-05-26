from allotment_update import excel_holdings
from Base import *
from common_foundation import *
from allotment_fetch import *

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
        try:
            holdings = fetch_allotment_holdings(user_id=client_id,password=password_user,totp_secret=topt_broker)
        except Exception as e:
            print(e)

        if holdings != 0:
            try:
                from win32comext.mapi import exchange
                excel_holdings(user_id=uci_user,security_symbol="x", exchange=exchange)
            except Exception as e:
                print(e)

        else:
            print("No allotment:",uci_user)