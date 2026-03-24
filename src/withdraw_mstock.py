# zerodha_withdraw.py
import re
import time
from Base import *
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional
from src.mstocks_base import get_mstock_otp


def withdraw_from_mstock(
        user_id: str,
        password: str,
        email_user: str,
        email_password: str,
        amount: float | int,
        headless: bool = False,
        timeout: int = 45000,
) -> tuple[bool, str]:


    amount_str = str(int(float(amount)))  # Zerodha usually wants whole numbers

    def run(playwright: Playwright) -> tuple[bool, str]:
        try:
            browser = playwright.chromium.launch(headless=False)
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
            page.goto("https://trade.mstock.com/#/login", wait_until="domcontentloaded")
            time.sleep(1)

            page.get_by_text("Login with Credentials").click()
            page.locator("#username").fill(user_id)
            page.locator("#username").press("Tab")
            page.locator("#password").fill(password)
            page.get_by_role("button", name="Login").click()



            time.sleep(1)
            # ── TOTP ────────────────────────────────────────────────
            sub1 = '(SUBJECT "Your login OTP")'
            otp1 = get_mstock_otp(email_user, email_password, sub1)
            print("OTP 1:", otp1)
            time.sleep(1)
            page.keyboard.type(otp1, delay=200)

            #Onw more line from codegen to Daily I understand warning click

            page.get_by_role("button", name="Continue").click()
            page.get_by_role("img", name="logo").click()
            page.get_by_role("button", name="Add Funds").click()
            page.get_by_role("tab", name="Withdraw").click()
            page.get_by_text("Withdrawable funds ₹").click()
            page.locator("b").click()
            page.get_by_text("Withdrawable funds ₹").click()
            page.get_by_role("textbox").click()
            page.get_by_role("textbox").fill(str(amount))
            page.get_by_role("button", name="Withdraw Funds").click()




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


# ── Example usage (when running this file directly) ────────────────
if __name__ == "__main__":
    success, msg = withdraw_from_mstock(
        user_id="7017307880",
        password="RamRate$1",
        amount=5,
        headless=False,  # change to True on server
    )
    print("Success:", success)
    print(msg)