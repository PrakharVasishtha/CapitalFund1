# sell_sme_ipo_above_open.py
# Sell 1 lot of specified SME IPO if current price >= 5% above opening price

import json
import pandas as pd
from dhanhq import DhanContext, dhanhq
import time
from Base import *

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────

CREDENTIALS_FILE = "credentials.json"  # from your previous multi-user setup
EXCEL_FILE       = "../share_data.xlsx"               # your Excel with SME IPO data
SHEET_NAME       = "u1"                         # change if needed

# Which symbol to monitor & auto-sell (change this or read dynamically)
TARGET_SYMBOL = "ABC SME"                           # exact trading symbol as in Dhan/Holdings

SELL_QTY_LOTS = 1                                   # always sell 1 lot
PROFIT_THRESHOLD = 1.05                             # 5% above open

# ────────────────────────────────────────────────
# Load credentials (reuse your multi-user loader)
# ────────────────────────────────────────────────

def load_credentials(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data.get("users", [])
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return []

# ────────────────────────────────────────────────
# Main logic
# ────────────────────────────────────────────────

def saler_sme_holdings():
    users = load_credentials(CREDENTIALS_FILE)
    if not users:
        print("No users found. Exiting.")
        return

    # Read Excel data


    for user in users:
        name = user.get("name", "User")
        client_id = user.get("client_id")
        access_token = user.get("access_token")
        uci = user.get("uci")

        if not client_id or not access_token:
            print(f"Skipping {name}: missing credentials")
            continue

        print(f"\n *********** Processing account: {name} ({client_id}) ************")

        SHEET_NAME = uci

        number_of_rows = get_last_row(EXCEL_FILE, SHEET_NAME)
        print(number_of_rows)
        if number_of_rows != 1:
            for r in range(2, number_of_rows + 2):
                print(f"---Processing row {r} ---")

                path = '../share_data.xlsx'
                wb = openpyxl.load_workbook(path)
                ws = wb[SHEET_NAME]
                smemb = ws.cell(r, 3).value
                print("smemb: ",smemb)
                if smemb == "sme":
                    symbol = ws.cell(r, 2).value
                    security_id = ws.cell(r, 4).value
                    quantity_on_listing = ws.cell(r, 5).value
                    lot_size = ws.cell(r, 6).value
                    number_of_lots = ws.cell(r, 7).value
                    total_sold = ws.cell(r, 8).value
                    open_price = ws.cell(r, 9).value

                    lots_to_sell =2


                    sell_qty = lot_size * lots_to_sell
                    print(f"Company {symbol} | Lot size: {lot_size} | Sell qty: {sell_qty}")
                    try:
                        dhan_context = DhanContext(client_id, access_token)
                        dhan = dhanhq(dhan_context)

                        # 1. Get holdings
                        holdings_resp = dhan.get_holdings()
                        if isinstance(holdings_resp, dict):
                            holdings = holdings_resp.get("data", [])
                        else:
                            holdings = holdings_resp or []

                        holding = next((h for h in holdings if h.get('tradingSymbol') == symbol), None)
                        if not holding:
                            print(f"  No holding of {symbol} in this account.")
                            continue

                        available_qty = int(holding.get('availableQty', 0))
                        total_qty = int(holding.get('totalQty', 0))
                        print(f"  Available qty: {available_qty} | Total qty: {total_qty}")

                        if available_qty < sell_qty:
                            sell_qty = available_qty
                            print(f"  Not enough available quantity (available_qty < sell_qty). new sell_qty: {sell_qty}")
                            continue

                        exchange_segment = holding.get('exchange')  # usually 'NSE' for SME

                        # Market quote (snapshot)
                        quote_resp = dhan.get_market_quote(security_id)
                        if not quote_resp or 'data' not in quote_resp:
                            print("  Failed to get market quote.")
                            continue

                        quote_data = quote_resp['data']
                        ltp = float(quote_data.get('ltp', 0))

                        if ltp <= 0:
                            print("  LTP not available.")
                            continue

                        ref_price = opening_price_from_excel if use_excel_open else open_price
                        if ref_price <= 0:
                            print("  Reference open price not available.")
                            continue

                        print(f"  LTP: ₹{ltp:.2f} | Open (ref): ₹{ref_price:.2f}")

                        if ltp >= ref_price * PROFIT_THRESHOLD:
                            print(f"  CONDITION MET! LTP {ltp:.2f} ≥ {ref_price * PROFIT_THRESHOLD:.2f}")

                            # 3. Place SELL order (CNC - delivery)
                            order_response = dhan.place_order(
                                security_id=security_id,
                                exchange_segment=dhan.NSE,              # or dhan.BSE if needed
                                transaction_type=dhan.SELL,
                                quantity=sell_qty,
                                order_type=dhan.MARKET,                 # or dhan.LIMIT with price=ltp
                                product_type=dhan.CNC,                  # delivery sell
                                price=0,                                # market order
                                trigger_price=0,
                                disclosed_quantity=0,
                                validity=dhan.DAY,                      # or dhan.IOC
                                remarks=f"Auto sell 1 lot {symbol} @ +5%"
                            )

                            if order_response.get('status') == 'success':
                                print(f"  SELL ORDER PLACED SUCCESSFULLY! Order ID: {order_response.get('orderId')}")
                            else:
                                print(f"  Order failed: {order_response}")

                        else:
                            print(f"  Not yet 5% above open. Skipping.")

                    except Exception as e:
                        print(f"  Error in account {name}: {str(e)}")

                    time.sleep(1)  # small delay between accounts

saler_sme_holdings()