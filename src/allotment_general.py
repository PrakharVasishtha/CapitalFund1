"""
allotment_general.py
====================
Orchestrates IPO allotment detection across all registered user accounts.

For each user in CAPITALFUND_USERS, this module:
  1. Calls fetch_allotment_holdings() to log into Zerodha Kite and check Holdings
     for any stock that is NOT one of the default SMWS ETFs.
  2. If a new allotment symbol is found, calls excel_holdings() to register it
     in allotted_holdings.xlsx and populate enrichment data (GMP, subscription,
     review, VIX).

Usage (standalone):
  python src/allotment_general.py
"""
from common_foundation import send_email_with_excel
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from allotment_update import excel_holdings
from Base import load_credentials
from allotment_fetch import fetch_allotment_holdings

CREDENTIALS_FILE = "credentials.json"


def ipo_allotment_manager():
    """
    Main orchestration function. Iterates over all user accounts and:
      - Fetches Zerodha Holdings, filtering out default SMWS ETFs and market indices.
      - If a new allotment symbol is detected, registers and enriches it in
        allotted_holdings.xlsx via excel_holdings().
      - Prints a summary message for each user.
    """
    print(
        "-----------ipo_allotment_manager----------")
    users = load_credentials(CREDENTIALS_FILE)
    for user in users:
        uci_user = user.get("uci")
        client_id = user.get("broker_client_id")
        password_user = user.get("password_broker")
        topt_broker = user.get("topt_broker")

        holdings = None
        try:
            holdings = fetch_allotment_holdings(
                user_id=client_id,
                password=password_user,
                totp_secret=topt_broker,
            )
            if holdings:
                print(f"Allotment found for {uci_user}: {holdings}")
        except Exception as e:
            print(f"ipo_allotment_manager: fetch_allotment_holdings failed for {uci_user}: {e}")

        if holdings:
            try:
                symbols = [holdings] if isinstance(holdings, (dict, str, tuple)) else holdings
                for sym_entry in symbols:
                    if isinstance(sym_entry, dict):
                        sym = sym_entry.get("symbol")
                        qty = sym_entry.get("quantity", 0)
                    elif isinstance(sym_entry, (list, tuple)) and len(sym_entry) >= 2:
                        sym = sym_entry[0]
                        qty = sym_entry[1]
                    else:
                        sym = str(sym_entry)
                        qty = 0

                    print(f"Processing allotment for {uci_user}: Symbol={sym}, Quantity={qty}")
                    excel_holdings(uci_user, holding_symbol=sym, shares_allocated=qty)
            except Exception as e:
                print(f"ipo_allotment_manager: excel_holdings failed for {uci_user}: {e}")
        else:
            print("No allotment found for user:", uci_user)
    try:
        send_email_with_excel(mail_subject="IPO Data Updated",mail_content="IPO Data Updated",path_of_file='allotted_holdings.xlsx')
    except Exception as e:
        print("Cant send allotted_holdings.xlsx")


if __name__ == "__main__":
    ipo_allotment_manager()
