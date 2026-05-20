import kotak_get_balance
import asyncio
import priority_ipo_smws_sell
from fund_bank_to_kite import withdraw_bank_to_kite
from Base import *

CREDENTIALS_FILE = "credentials.json"


def fund_trf_to_kite():
    print(
        "*************************************-----------fund_trf_to_kite----------************************************")
    print(
        "##############################################################################################################")
    d0 = priority_ipo_smws_sell.ipo_required_fund(0)
    d1 = priority_ipo_smws_sell.ipo_required_fund(1)
    required_fund = d0 + d1
    if True:
        users = load_credentials(CREDENTIALS_FILE)
        # Users
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
                #balance = 600
                balance = asyncio.run \
                    (kotak_get_balance.get_kotak_balance(USER_ID=bank_user ,PASSWORD=bank_password ,EMAIL_USR=email_user
                                                        ,EMAIL_PSS= email_password))
            except Exception as e:
                print(e)
                balance = 0
            final_amount = 0
            if required_fund > balance:
                final_amount = 0
            else:
                final_amount = balance - required_fund
            print("final_required_amount" ,final_amount)
            if final_amount > 500:
                success, message = withdraw_bank_to_kite(user_uci=uci_user,broker_id=client_id,broker_password=password_user,totp_secret=topt_broker,bank_id=bank_user,bank_password=bank_password,EMAIL_USR=email_user,EMAIL_PSS=email_password,amount=final_amount,)
                print(success, message)
            else:
                print("No withdrawal required.")


#print(fund_trf_to_kite())