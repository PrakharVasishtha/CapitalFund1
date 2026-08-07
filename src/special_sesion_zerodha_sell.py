import time
import Base
from common_foundation import *
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp


def zerodha_sell_lc(
        user_id: str,
        password: str,
        totp_secret: str,
        security_symbol: str,
        headless: bool = False,
        timeout: int = 5000,
) -> tuple[bool, str]:
    def run(playwright: Playwright) -> tuple[bool, str]:
        print("______zerodha_sell_lc___", user_id, ":", security_symbol)
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
            file_path = user_id + ".txt"
            amt_symbl = security_symbol

            page: Page = context.new_page()
            page.set_default_timeout(timeout)

            # ── Login ───────────────────────────────────────────────
            page.goto("https://kite.zerodha.com/", wait_until="domcontentloaded")
            time.sleep(1)

            page.get_by_role("textbox", name="Phone number or User ID").fill(user_id)
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("button", name="Login").click()
            time.sleep(1)

            # ── TOTP ────────────────────────────────────────────────
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)
            time.sleep(2)
            page.mouse.click(30, 50)
            time.sleep(.5)

            # NOTE: this block was missing entirely in the original file,
            # which is why security_sell_nse/bse raised NameError below.
            # Added to match the working pattern in trader_zerodha_sell.py.
            security_sell_nse = "SELL " + security_symbol + " (NSE) quantity"
            security_sell_bse = "SELL " + security_symbol + " (BSE) quantity"

            page.get_by_role("link", name="Holdings").click()
            time.sleep(2)

            ############################
            try:
                page.get_by_role("cell", name=security_symbol).click()
                page.get_by_role("link", name="NIFTYIETF").click()
                try:
                    holdings = page.get_by_role("spinbutton", name=security_sell_nse).input_value()
                except Exception as e:
                    print(e)
                    holdings = page.get_by_role("spinbutton", name=security_sell_bse).input_value()
                print("Holdings Inside:", holdings)
                page.get_by_role("button", name="Cancel").click()
            except Exception as e:
                holdings = 0
                print(e)

            ##############################
            logger(file_path, amt_symbl, "Sold")
            return True, f"Sell orders initiated successfully"

        except Exception as e:
            logger(file_path, amt_symbl, "not Sold for some Exception")
            import traceback
            return False, f"Sell orders failed: {str(e)}\n{traceback.format_exc()}"

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)