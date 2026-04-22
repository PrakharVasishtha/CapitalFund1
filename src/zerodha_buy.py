# zerodha_withdraw.py
import re
import time
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional


def zerodha_buy(
        user_id: str,
        password: str,
        totp_secret: str,
        amount: float | int,

        headless: bool = True,
        timeout: int = 45000,
) -> tuple[bool, str]:

    amount_str = str(int(float(amount)))  # Zerodha usually wants whole numbers

    def run(playwright: Playwright) -> tuple[bool, str]:
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


            page.get_by_role("textbox", name="Phone number or User ID").fill(user_id)
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("button", name="Login").click()
            time.sleep(1)
            # ── TOTP ────────────────────────────────────────────────
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)

            # Buy
            page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").click()
            page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").fill("1")
            page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").press("Tab")
            page.get_by_role("spinbutton", name="Price", exact=True).press("ControlOrMeta+c")
            page.get_by_role("spinbutton", name="Price", exact=True).fill("275")
            page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
            page.get_by_role("button", name="Buy").click()
            page.get_by_role("button", name="Cancel").click()




            return True, f"Withdrawal initiated successfully"

        except Exception as e:
            import traceback
            return False, f"Withdrawal failed: {str(e)}\n{traceback.format_exc()}"

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)
