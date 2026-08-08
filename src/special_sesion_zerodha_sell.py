import time
import Base
from common_foundation import logger
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp


def zerodha_sell_lc(
        user_id: str,
        password: str,
        totp_secret: str,
        security_symbol: str,
        shares_quantity: int = 0,
        exchange: str = "NSE",
        issue_price: float = 0.0,
        headless: bool = False,
        timeout: int = 15000,
) -> tuple[bool, str]:
    """
    Logs into Zerodha Kite, navigates to Holdings, and places a Sell Order
    at Lower Circuit for the specified security_symbol and quantity.
    """
    def run(playwright: Playwright) -> tuple[bool, str]:
        print(f"______zerodha_sell_lc___ User: {user_id} | Symbol: {security_symbol} | Qty: {shares_quantity} | Exch: {exchange}")
        if not user_id or not password or not totp_secret:
            return False, f"Missing credentials for user {user_id}"

        file_path = user_id + ".txt"
        amt_symbl = security_symbol

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

            # ── 1. Login ───────────────────────────────────────────────
            page.goto("https://kite.zerodha.com/", wait_until="domcontentloaded")
            time.sleep(1)

            page.get_by_role("textbox", name="Phone number or User ID").fill(str(user_id))
            page.get_by_role("textbox", name="Password").fill(str(password))
            page.get_by_role("button", name="Login").click()
            time.sleep(1)

            # ── 2. TOTP ────────────────────────────────────────────────
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)
            time.sleep(2)
            page.mouse.click(30, 50)
            time.sleep(0.5)

            # ── 3. Navigate to Holdings ────────────────────────────────
            try:
                page.goto("https://kite.zerodha.com/holdings", wait_until="domcontentloaded")
            except Exception:
                page.get_by_role("link", name="Holdings").click()
            time.sleep(2)

            security_sell_nse = f"SELL {security_symbol} (NSE) quantity"
            security_sell_bse = f"SELL {security_symbol} (BSE) quantity"

            holdings_qty = shares_quantity
            # If quantity not provided, fetch from Holdings page
            if holdings_qty <= 0:
                try:
                    page.get_by_role("cell", name=security_symbol).click()
                    page.get_by_role("link", name="NIFTYIETF").click()
                    try:
                        h_val = page.get_by_role("spinbutton", name=security_sell_nse).input_value()
                    except Exception:
                        h_val = page.get_by_role("spinbutton", name=security_sell_bse).input_value()
                    page.get_by_role("button", name="Cancel").click()
                    holdings_qty = int(float(h_val))
                except Exception as e:
                    print(f"Could not read holdings qty for {security_symbol}: {e}")
                    holdings_qty = 0

            if holdings_qty <= 0:
                return False, f"Zero holdings found for {security_symbol}"

            print(f"Placing LC sell order for {security_symbol}: {holdings_qty} shares...")

            # ── 4. Open Order Window & Place Order ────────────────────
            try:
                page.get_by_role("cell", name=security_symbol).hover()
                time.sleep(0.3)
                page.keyboard.press("S")
            except Exception:
                page.keyboard.press("S")

            time.sleep(1)
            try:
                page.get_by_text("Regular").click()
            except Exception:
                pass

            # Fill Quantity
            qty_filled = False
            for target_label in [security_sell_nse, security_sell_bse, "Quantity"]:
                try:
                    spin = page.get_by_role("spinbutton", name=target_label)
                    if spin.is_visible():
                        spin.click()
                        spin.fill(str(holdings_qty))
                        qty_filled = True
                        break
                except Exception:
                    pass

            if not qty_filled:
                page.keyboard.type(str(holdings_qty))

            # Set Limit order with Lower Circuit price (0.05 / minimum price)
            try:
                page.get_by_text("Limit").click()
                time.sleep(0.5)
                lc_price = "0.05"
                price_spin = page.get_by_role("spinbutton", name="Price", exact=True)
                if price_spin.is_visible():
                    price_spin.click()
                    price_spin.press("ControlOrMeta+a")
                    price_spin.fill(lc_price)
            except Exception as e:
                print(f"Limit price setting note: {e}")

            # ── 5. Submit Order ────────────────────────────────────────
            time.sleep(1)
            page.get_by_role("button", name="Sell").click()
            time.sleep(2)

            logger(file_path, amt_symbl, f"Sold {holdings_qty} @ LC")
            return True, f"Successfully placed LC sell order for {holdings_qty} shares of {security_symbol}"

        except Exception as e:
            logger(file_path, amt_symbl, f"LC Sell Exception: {e}")
            import traceback
            return False, f"LC sell failed for {security_symbol}: {e}\n{traceback.format_exc()}"

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)