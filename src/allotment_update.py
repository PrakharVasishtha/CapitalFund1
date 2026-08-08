"""
allotment_update.py
===================
Updates allotted_holdings.xlsx with IPO enrichment data for newly detected allotments.

Key functions:
  get_allotted_holdings_path()  -- Resolves the absolute path to allotted_holdings.xlsx
                                   regardless of the current working directory.
  excel_holdings(usr_id, holding_symbol)
    - If holding_symbol is provided and not already in the user's sheet, appends a new row
      with special_session_status = 5 (pending enrichment).
    - Iterates rows with special_session_status == 5 and fetches:
        GMP (column 28)      : Grey Market Premium from Chittorgarh
        Review (column 23)   : Analyst review risk flag (1 = risky, 0 = safe)
        Subscription (24-26) : Retail / NII / QIB subscription levels
        India VIX (column 35): Market volatility index from Yahoo Finance
    - Saves enriched data back to allotted_holdings.xlsx.

Column reference for allotted_holdings.xlsx (1-indexed, Row 1 = header):
  Col 1  : security_name
  Col 7  : special_session_status (0=not started, 1=started, 2=sold, 3=unsold, 5=pending)
  Col 10 : regular_session_status (0=not started, 2=sold, 3=unsold, 4=transferred)
  Col 23 : review score
  Col 24 : retail subscription
  Col 25 : NII subscription
  Col 26 : QIB subscription
  Col 28 : GMP
  Col 35 : India VIX
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from allotment_fetch import fetch_allotment_holdings
import openpyxl
import time
from Base import get_vix
from ipo_ExtractGMP import get_ipo_gmp
from ipo_ExtractReview import has_dicey_word
from ipo_ExtractSubscription import get_ipo_subscription_live
from datetime import date


import os


def get_allotted_holdings_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "allotted_holdings.xlsx")
    if os.path.exists(path):
        return path
    if os.path.exists("allotted_holdings.xlsx"):
        return "allotted_holdings.xlsx"
    return path


def excel_holdings(usr_id: str, holding_symbol: str = None):
    """
    Scans the user's sheet in allotted_holdings.xlsx for rows where
    special_session_status == 5 (per readme.md: "empty" / not yet fetched)
    and fills in GMP / subscription / review / VIX data for those rows.
    If holding_symbol is provided, ensures it exists in the sheet first.
    """
    print("excel_holdings", usr_id)
    path = get_allotted_holdings_path()
    if not os.path.exists(path):
        print(f"excel_holdings Error: File not found at '{path}'")
        return

    try:
        wb = openpyxl.load_workbook(path)
    except Exception as e:
        print(f"excel_holdings Error opening workbook '{path}': {e}")
        return

    sheet_name = str(usr_id)
    if sheet_name not in wb.sheetnames:
        print(f"excel_holdings Error: Sheet '{sheet_name}' not found in '{path}'. Available sheets: {wb.sheetnames}")
        wb.close()
        return

    ws = wb[sheet_name]

    # If a holding_symbol was detected, check if it's already in the sheet
    if holding_symbol:
        holding_symbol = str(holding_symbol).strip()
        existing_symbols = [
            str(ws.cell(r, 1).value).strip().upper() 
            for r in range(2, ws.max_row + 1) 
            if ws.cell(r, 1).value
        ]
        if holding_symbol.upper() not in existing_symbols:
            next_row = ws.max_row + 1
            ws.cell(next_row, 1, holding_symbol)
            ws.cell(next_row, 7, 5)
            try:
                wb.save(path)
                print(f"excel_holdings: Appended new holding '{holding_symbol}' at row {next_row}")
            except Exception as e:
                print(f"excel_holdings Error saving new holding row: {e}")

    max_r = max(ws.max_row, 20)
    for k in range(2, max_r + 1):
        status_cell = ws.cell(k, 7).value
        if status_cell is None:
            continue

        try:
            spl_session_status = int(status_cell)
        except (ValueError, TypeError):
            continue

        if spl_session_status != 5:
            continue

        name1 = ws.cell(k, 1).value
        if name1 is None or str(name1).strip() == "" or str(name1).strip() == "None":
            continue

        name1 = str(name1).strip()
        print(f"Processing row {k}: {name1}")

        url2 = f"https://www.chittorgarh.com/ipo/{name1.lower().replace(' ', '-')}-ipo/"

        try:
            gmp = get_ipo_gmp(name1)
        except Exception as e:
            print(f"excel_holdings: GMP fetch failed at row {k}: {e}")
            gmp = 0

        try:
            sub = get_ipo_subscription_live(url2)
            if sub is None:
                sub = [0, 0, 0, 0]
        except Exception as e:
            print(f"excel_holdings: subscription fetch failed at row {k}: {e}")
            sub = [0, 0, 0, 0]

        try:
            review = int(has_dicey_word(url2))
        except Exception as e:
            print(f"excel_holdings: review fetch failed at row {k}: {e}")
            review = 1

        try:
            AI = get_vix()
        except Exception as e:
            AI = 0

        ws.cell(k, 28, gmp)
        ws.cell(k, 23, review)
        ws.cell(k, 24, sub[0] if len(sub) > 0 else 0)
        ws.cell(k, 25, sub[1] if len(sub) > 1 else 0)
        ws.cell(k, 26, sub[2] if len(sub) > 2 else 0)
        ws.cell(k, 35, AI)

        try:
            wb.save(path)
            print(f"excel_holdings: Successfully updated details for row {k} ({name1})")
        except PermissionError:
            print(f"excel_holdings Error: Permission denied. Please ensure '{path}' is closed.")
        except Exception as e:
            print(f"excel_holdings An error occurred while saving the file: {e}")

    wb.close()


def allotment_update():
    from Base import load_credentials
    users = load_credentials("credentials.json")
    for user in users:
        client_id = user.get("broker_client_id")
        password_user = user.get("password_broker")
        topt_broker = user.get("topt_broker")
        if client_id and password_user and topt_broker:
            fetch_allotment_holdings(
                user_id=client_id,
                password=password_user,
                totp_secret=topt_broker,
            )