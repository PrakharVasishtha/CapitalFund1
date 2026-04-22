from src.Base import load_credentials
from src.zerodha_buy import zerodha_buy


def smws_buyer():
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?output=csv"
    df0 = pd.read_csv(url_csv)
    time.sleep(1)
    df = pd.read_csv(url_csv)
    buynifty = df.iloc[23, 3]
    # print("buynifty:", buynifty)
    goldetfbuy = df.iloc[26, 3]
    # print("goldetfbuy:", goldetfbuy)
    silveretfbuy = df.iloc[29, 3]
    # print("silveretfbuy:", silveretfbuy)

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
            buy_amount = 0
            if int(buynifty) == 1:
                zerodha_buy(user_id: str,
        password: str,
        totp_secret: str,
        amount: float | int)