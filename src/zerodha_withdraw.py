# zerodha_withdraw.py
import re
import time

from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional


def withdraw_from_zerodha(
        user_id: str,
        password: str,
        totp_secret: str,
        amount: float | int,
        headless: bool = True,
        timeout: int = 45000,
) -> tuple[bool, str]:
    """
    Automates withdrawal of funds from Zerodha Kite → Console.

    Args:
        user_id:      Zerodha client code (e.g. "MFB802")
        password:     Zerodha login password
        totp_secret:  Base32 TOTP secret (Google Authenticator / Authy key)
        amount:       Amount to withdraw (will be converted to str)
        headless:     Run browser without UI (recommended: True in production)
        timeout:      Playwright action timeout in milliseconds

    Returns:
        tuple[bool, str]: (success, message)
    """
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
            wihtdrawable = withdraw_page.get_by_text("₹").nth(4).inner_text()
            clean_wihtdrawable = wihtdrawable.replace("₹", "").split(".")[0]
            print(clean_wihtdrawable)
            time.sleep(1)
            # ── Enter amount & confirm ──────────────────────────────
            eq_input = withdraw_page.locator("#eq_input")
            eq_input.wait_for(state="visible", timeout=15000)
            eq_input.click()
            eq_input.fill(amount_str)

            withdraw_page.get_by_role("button", name="Continue").click()
            withdraw_page.get_by_role("button", name="Confirm").click()

            # Give some time for confirmation (you can improve this)
            withdraw_page.wait_for_timeout(4000)

            return True, f"Withdrawal of ₹{amount_str} initiated successfully"

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
    success, msg = withdraw_from_zerodha(
        user_id="MFB802",
        password="RamRate$1",
        totp_secret="DOIIMB2PTIIOCKDQ4ILOCPVF44YJ7QBU",
        amount=5,
        headless=False,  # change to True on server
    )
    print("Success:", success)
    print(msg)