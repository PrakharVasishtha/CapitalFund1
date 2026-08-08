"""
allotment_fetch.py
==================
Logs into each Zerodha Kite account via Playwright and detects newly allotted
IPO stocks by scanning the Holdings page.

Default holdings (SMWS ETFs) and market index tickers are automatically excluded.
Only stocks that are NOT in DEFAULT_HOLDINGS or INDEX_SYMBOLS are returned.

Returns:
  str  -- single new symbol (e.g. 'SWIGGY') if exactly one is found
  list -- list of symbols if multiple are found
  None -- if no new allotment holdings detected

Functions:
  fetch_allotment_holdings(user_id, password, totp_secret, security_symbol, ...)
"""
import time
import Base
from common_foundation import logger
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp

DEFAULT_HOLDINGS = {"NIFTYIETF", "TATAGOLD", "TATSILV"}
INDEX_SYMBOLS = {
    "NIFTY 50", "NIFTY50", "SENSEX", "BSE SENSEX",
    "NIFTY BANK", "BANKNIFTY", "NIFTY", "FINNIFTY", "MIDCPNIFTY",
    "NIFTY FIN SERVICE"
}


def fetch_allotment_holdings(
        user_id: str = None,
        password: str = None,
        totp_secret: str = None,
        security_symbol: str = None,
        headless: bool = False,
        timeout: int = 15000,
):
    """
    Logs into Zerodha Kite, navigates to Holdings, excludes default holdings
    (NIFTYIETF, TATAGOLD, TATSILV) and market indices (NIFTY 50, SENSEX),
    and returns the symbol(s) of any other holdings found.
    """
    def run(playwright: Playwright):
        print("______fetch_allotment_holdings___", user_id)
        if not user_id or not password or not totp_secret:
            print(f"Error: Missing credentials for fetch_allotment_holdings (user_id={user_id})")
            return None

        file_path = f"{user_id}.txt"
        amt_symbl = security_symbol or "ALLOTMENT"

        try:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                )
            )

            page: Page = context.new_page()
            page.set_default_timeout(timeout)

            # ── Login ───────────────────────────────────────────────
            page.goto("https://kite.zerodha.com/", wait_until="domcontentloaded")
            time.sleep(1)

            page.get_by_role("textbox", name="Phone number or User ID").fill(str(user_id))
            page.get_by_role("textbox", name="Password").fill(str(password))
            page.get_by_role("button", name="Login").click()
            time.sleep(1)

            # ── TOTP ────────────────────────────────────────────────
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)
            time.sleep(2)

            # ── Navigate to Holdings ────────────────────────────────
            try:
                page.goto("https://kite.zerodha.com/holdings", wait_until="domcontentloaded")
            except Exception:
                page.get_by_role("link", name="Holdings").click()
            time.sleep(2)

            # ── Extract holding symbols & quantities ──────────────────
            raw_holdings = page.evaluate(r"""() => {
                const holdings = [];
                const holdingsContainer = document.querySelector(".holdings, .holdings-table, div.holdings, .table-wrapper");
                const container = holdingsContainer || document;

                const rows = container.querySelectorAll("tbody tr");
                rows.forEach(row => {
                    if (row.closest(".market-overview") || row.closest("header") || row.closest(".header")) {
                        return;
                    }
                    const cell = row.querySelector("td.instrument, td:first-child");
                    if (cell) {
                        const symbolSpan = cell.querySelector(".tradingsymbol, .instrument-name, span");
                        const txt = ((symbolSpan ? symbolSpan.innerText : cell.innerText) || "").trim();
                        if (txt) {
                            const sym = txt.split("\n")[0].trim();
                            const qtyCell = row.querySelector("td.quantity, td.qty, td:nth-child(2)");
                            let qty = 0;
                            if (qtyCell) {
                                const qTxt = (qtyCell.innerText || "").replace(/,/g, "").trim();
                                const parsed = parseInt(qTxt, 10);
                                if (!isNaN(parsed)) qty = parsed;
                            }
                            if (sym) holdings.push({symbol: sym, quantity: qty});
                        }
                    }
                });

                return holdings;
            }""")

            ignored_words = {
                "INSTRUMENT", "SYMBOL", "QTY.", "QTY", "TOTAL",
                "HOLDINGS", "DISCREPANT", "CUR. VAL", "P&L", "AVG. COST",
                "CUR.VAL", "AVG.COST", "DAY'S P&L", "UNREALISED P&L", "REALISED P&L"
            }

            cleaned_holdings = []
            seen_symbols = set()
            for item in raw_holdings:
                sym = item.get("symbol", "").strip().upper()
                qty = item.get("quantity", 0)
                if (
                    sym 
                    and sym not in ignored_words 
                    and sym not in DEFAULT_HOLDINGS 
                    and sym not in INDEX_SYMBOLS
                ):
                    if sym not in seen_symbols:
                        seen_symbols.add(sym)
                        cleaned_holdings.append({"symbol": sym, "quantity": qty})

            print(f"Other holdings found for {user_id}: {cleaned_holdings}")

            # If specific security_symbol requested, check quantity
            if security_symbol:
                security_nse = "SELL " + security_symbol + " (NSE) quantity"
                security_bse = "SELL " + security_symbol + " (BSE) quantity"
                holdings_qty = 0
                try:
                    page.get_by_role("cell", name=security_symbol).click()
                    page.get_by_role("link", name="NIFTYIETF").click()
                    try:
                        holdings_qty = page.get_by_role("spinbutton", name=security_nse).input_value()
                    except Exception as e:
                        print(e)
                        holdings_qty = page.get_by_role("spinbutton", name=security_bse).input_value()
                    page.get_by_role("button", name="Cancel").click()
                except Exception as e:
                    print(e)
                    holdings_qty = 0
                return holdings_qty

            if not cleaned_holdings:
                return None
            elif len(cleaned_holdings) == 1:
                return cleaned_holdings[0]
            else:
                return cleaned_holdings

        except Exception as e:
            logger(file_path, amt_symbl, f"Exception in fetch_allotment_holdings: {e}")
            import traceback
            print(traceback.format_exc())
            return None

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)