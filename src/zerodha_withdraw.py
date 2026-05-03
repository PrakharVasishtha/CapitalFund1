# zerodha_withdraw.py
import re
import time
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional


def withdraw_from_zerodha(
        user_id: str,
        password: str,
        totp_secret: str,
        amount: float | int,
        headless: bool = False,
        timeout: int = 45000,
) -> tuple[bool, str]:

    amount_str = str(int(float(amount)))  # Zerodha usually wants whole numbers

    def run(playwright: Playwright) -> tuple[bool, str]:
        print(user_id,"reqrd to withdrw frm zerodha",amount)
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

            # Wait for dashboard to load
            page.get_by_role("link", name="Funds").click()
            time.sleep(1)
            # ── Open withdrawal popup ───────────────────────────────
            with page.expect_popup() as popup_info:
                page.get_by_role("link", name="Withdraw").click()

            withdraw_page: Page = popup_info.value
            withdraw_page.wait_for_load_state("domcontentloaded")

            # Sometimes Zerodha redirects or opens console directly
            if "console.zerodha.com" not in withdraw_page.url:
                withdraw_page.goto("https://console.zerodha.com/funds/overview?src=kiteweb")
            time.sleep(1)
            wihtdrawable = withdraw_page.get_by_text("₹").nth(5).inner_text()
            print(wihtdrawable)
            clean_wihtdrawable = wihtdrawable.replace("₹", "").split(".")[0]
            clean_wihtdrawable = Base.parse_float(clean_wihtdrawable)
            print("clean_wihtdrawable",clean_wihtdrawable)
            print("required amount", amount)
            #print("Type", type(amount))
            amount_float = float(amount)
            print("amount_float", amount_float)
            #final_amount = 1.0
            #zerodha balance limit
            if clean_wihtdrawable < amount_float:
                final_amount = clean_wihtdrawable
            else:
                final_amount = amount_float

            # zerodha 2 lakh instant limit
            if final_amount > 200000:
                final_amount = 200000
            else:
                print("final_amount within limit")

            print("final_amount",final_amount)
            time.sleep(1)
            # ── Enter amount & confirm ──────────────────────────────
            if final_amount >= 1:
                eq_input = withdraw_page.locator("#eq_input")
                eq_input.wait_for(state="visible", timeout=15000)
                eq_input.click()
                amount_str = str(int(float(final_amount)))
                print("amount_str",amount_str)
                eq_input.fill(amount_str)
                withdraw_page.get_by_role("button", name="Continue").click()
                withdraw_page.get_by_role("button", name="Confirm").click()

                # Give some time for confirmation (you can improve this)
                withdraw_page.wait_for_timeout(4000)
            else:
                print("less than 1 amount, so no withdrawal")

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
