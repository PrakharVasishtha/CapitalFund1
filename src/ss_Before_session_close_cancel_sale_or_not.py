"""
special_session_monitor.py
===========================
Monitors pre-open / indicative prices of IPO stocks on listing day between 09:00 AM and 09:45 AM.
If loss/discount thresholds are hit, triggers special pre-open sell orders via Zerodha Kite.
"""
import sys
import os
import time
import openpyxl
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Base import load_credentials
from allotment_update import get_allotted_holdings_path
from special_session_indicative_price_nse import get_ipo_indicative_price
from special_sesion_zerodha_sell import zerodha_sell_lc

CREDENTIALS_FILE = "credentials.json"


def special_session_monitor():
    """
    Main loop to monitor IPO indicative prices during the pre-open listing window (09:00 - 09:45 AM).
    Iterates over user holding records in allotted_holdings.xlsx and checks IEP against issue price.
    """
    print("-----------special_session_monitor---------")

    users = load_credentials(CREDENTIALS_FILE)
    if not users:
        print("special_session_monitor: No user credentials found.")
        return

    excel_path = get_allotted_holdings_path()
    if not os.path.exists(excel_path):
        print(f"special_session_monitor: Excel file not found at '{excel_path}'")
        return

    now = datetime.now()
    # Active monitoring window: 09:00 AM to 09:45 AM
    time_flag = (now.hour == 9 and 0 <= now.minute <= 45)

    # If executed outside 09:00-09:45 AM, run a single test pass so user can inspect output
    single_pass = not time_flag
    if single_pass:
        print("Note: Running outside 09:00-09:45 AM window. Performing a single monitoring pass...")

    while True:
        try:
            wb = openpyxl.load_workbook(excel_path)
        except Exception as e:
            print(f"special_session_monitor: Error loading workbook '{excel_path}': {e}")
            break

        file_changed = False

        for user in users:
            uci_user = str(user.get("uci"))
            client_id = user.get("broker_client_id")
            password_user = user.get("password_broker")
            totp_broker = user.get("topt_broker") or user.get("totp_broker")

            if uci_user not in wb.sheetnames:
                continue

            ws = wb[uci_user]

            for r in range(2, ws.max_row + 1):
                security_symbol = ws.cell(r, 1).value
                if not security_symbol or str(security_symbol).strip().lower() in ["none", ""]:
                    continue

                security_symbol = str(security_symbol).strip()
                lot_size = ws.cell(r, 2).value or 1
                try:
                    lot_size = int(lot_size)
                except (ValueError, TypeError):
                    lot_size = 1

                issue_price = ws.cell(r, 3).value or 0.0
                try:
                    issue_price = float(issue_price)
                except (ValueError, TypeError):
                    issue_price = 0.0

                exchange = str(ws.cell(r, 6).value or "NSE").strip().upper()
                status_cell = ws.cell(r, 7).value

                try:
                    spl_status = int(status_cell) if status_cell is not None else 0
                except (ValueError, TypeError):
                    spl_status = 0

                # Status 2 = Sold, Status 3 = Unsold / Done monitoring
                if spl_status in [2, 3]:
                    continue

                category = "sme" if lot_size >= 100 else "mb"

                print(f"\nChecking [{uci_user}] Symbol: '{security_symbol}' | Exchange: {exchange} | Issue Price: {issue_price} | Category: {category}")

                # Fetch pre-open indicative price
                try:
                    price_info = get_ipo_indicative_price(symbol=security_symbol, exchange=exchange)
                except Exception as e:
                    print(f"Error fetching indicative price for {security_symbol}: {e}")
                    price_info = {"indicative_price": 0.0}

                indicative_price = price_info.get("indicative_price", 0.0) if isinstance(price_info, dict) else float(price_info or 0.0)
                print(f"Result for {security_symbol}: IEP = {indicative_price}")

                loss_percent = 0.0
                if issue_price > 0 and indicative_price > 0 and issue_price > indicative_price:
                    loss_percent = ((issue_price - indicative_price) / issue_price) * 100.0

                print(f"Calculated discount/loss %: {loss_percent:.2f}%")

                # Decision rules
                should_sell = False
                if category == "sme" and loss_percent > 0:
                    should_sell = True
                elif category == "mb" and loss_percent > 11.9:
                    should_sell = True

                if should_sell:
                    print(f"Triggering sell order for {security_symbol} (User: {uci_user}, Loss %: {loss_percent:.2f}%)...")
                    if client_id and password_user and totp_broker:
                        try:
                            success, msg = zerodha_sell_lc(
                                user_id=client_id,
                                password=password_user,
                                totp_secret=totp_broker,
                                security_symbol=security_symbol
                            )
                            print(f"Sell execution output: {msg}")
                            if success:
                                ws.cell(r, 7, 2)  # Status 2 = Sold
                                file_changed = True
                        except Exception as e:
                            print(f"Failed to execute sell for {security_symbol}: {e}")
                    else:
                        print(f"Missing credentials for {uci_user}, cannot trigger sell order.")
                else:
                    print(f"No sell trigger for {security_symbol}.")

        if file_changed:
            try:
                wb.save(excel_path)
                print("special_session_monitor: Saved status updates to allotted_holdings.xlsx")
            except Exception as e:
                print(f"special_session_monitor: Error saving workbook: {e}")

        wb.close()

        if single_pass:
            print("Single pass completed.")
            break

        current_now = datetime.now()
        if not (current_now.hour == 9 and 0 <= current_now.minute <= 45):
            print("Time window (09:00 - 09:45 AM) ended. Exiting special_session_monitor.")
            break

        time.sleep(10)


if __name__ == "__main__":
    special_session_monitor()