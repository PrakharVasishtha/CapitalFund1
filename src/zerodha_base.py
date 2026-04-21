import os
import json
import logging
import pyotp
import requests
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect
from datetime import datetime

# ------------------- CONFIG -------------------
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "access_token.txt"


def generate_access_token():
    """Generate fresh access token using credentials.json"""
    users = load_credentials(CREDENTIALS_FILE)
    # Users
    for user in users:
        user_id = user.get("broker_client_id")
        password = user.get("password_broker")
        totp_secret = user.get("topt_broker")
        api_key = user.get["api_key"]
        api_secret = user.get["api_secret"]




    kite = KiteConnect(api_key=api_key)
    session = requests.Session()

    try:
        logging.info(f"🔄 Starting access token generation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Step 1: Login
        login_response = session.post(
            "https://kite.zerodha.com/api/login",
            data={"user_id": user_id, "password": password}
        )

        if login_response.status_code != 200:
            logging.error(f"Login failed: {login_response.text}")
            return None

        # Step 2: Two-factor authentication with TOTP
        totp = pyotp.TOTP(totp_secret).now()
        logging.info(f"Generated TOTP: {totp}")

        twofa_response = session.post(
            "https://kite.zerodha.com/api/twofa",
            data={
                "user_id": user_id,
                "request_id": login_response.json().get("request_id"),
                "twofa_value": totp
            }
        )

        if twofa_response.status_code != 200:
            logging.error(f"2FA failed: {twofa_response.text}")
            return None

        # Step 3: Get request_token from login URL
        login_url = kite.login_url()
        final_response = session.get(login_url, allow_redirects=True)

        parsed_url = urlparse(final_response.url)
        request_token = parse_qs(parsed_url.query).get("request_token", [None])[0]

        if not request_token:
            logging.error("❌ Could not extract request_token from redirect URL")
            return None

        logging.info("✅ Request token received")

        # Step 4: Generate access token
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]

        # Save token to file
        with open(TOKEN_FILE, "w") as f:
            f.write(access_token)

        logging.info(f"🎉 Access token generated successfully!")
        logging.info(f"Token saved to: {TOKEN_FILE}")
        logging.info(f"Token (first 15 chars): {access_token[:15]}...")

        return access_token

    except Exception as e:
        logging.error(f"❌ Error generating access token: {e}")
        return None


# ------------------- Main Execution -------------------
if __name__ == "__main__":
    print("🚀 Zerodha Daily Access Token Generator")
    print("=" * 50)

    access_token = generate_access_token()

    if access_token:
        print("\n✅ SUCCESS: Access token is ready for trading scripts!")
        print(f"   Token file: {TOKEN_FILE}")
        print(f"   Log file: zerodha_token.log")
    else:
        print("\n❌ FAILED: Check zerodha_token.log for details")