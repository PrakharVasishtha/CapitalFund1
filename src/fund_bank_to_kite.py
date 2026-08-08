import time
import openpyxl
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp

def withdraw_bank_to_kite(
        user_uci: int,
        broker_id: str,
        broker_password: str,
        totp_secret: str,
        bank_id: str,
        bank_password: str,
        EMAIL_USR: str,
        EMAIL_PSS: str,
        amount: float | int,
        headless: bool = False,
        timeout: int = 5000,
) -> tuple[bool, str]:

    def run(playwright: Playwright) -> tuple[bool, str]:
        print(user_uci, "reqrd to withdrw frm zerodha", amount)
        amount_str = str(amount)
        msg_log = "e"
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

            page.get_by_role("textbox", name="Phone number or User ID").fill(broker_id)
            page.get_by_role("textbox", name="Password").fill(broker_password)
            page.get_by_role("button", name="Login").click()
            time.sleep(1)
            # ── TOTP ────────────────────────────────────────────────
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)

            # Wait for dashboard to load
            page.get_by_role("link", name="Funds").click()
            time.sleep(1)

            with page.expect_popup() as page1_info:
                page.get_by_role("button", name="Add funds").click()
            page1 = page1_info.value
            page1.get_by_role("textbox", name="Enter amount").fill(amount_str)
            page1.get_by_text("Net banking₹9 + GST").click()
            page1.get_by_role("button", name="Continue").click()
            time.sleep(3)
            
            page1.get_by_role("link", name="CRN").click()
            page1.get_by_role("spinbutton", name="Enter CRN or Customer ID").click()
            page1.get_by_role("spinbutton", name="Enter CRN or Customer ID").fill(bank_id)
            page1.get_by_role("spinbutton", name="Enter CRN or Customer ID").press("Tab")
            page1.get_by_role("textbox", name="Select Bank Select Bank").click()
            page1.get_by_role("textbox", name="Select Bank Select Bank").fill(bank_password)

            page1.get_by_role("link", name="SECURE LOGIN").click()
            sub = '(SUBJECT "SMS2EMAIL" UNSEEN)'
            otp1 = Base.get_netbanking_otp_sms(EMAIL_USR, EMAIL_PSS, sub)
            page1.locator("#dynamic-access").click()
            page1.locator("#dynamic-access").click()
            page1.locator("#dynamic-access").click()
            page1.locator("#dynamic-access").fill(otp1)
            page1.get_by_role("link", name="Verify").click()
            page1.get_by_role("link", name="CONFIRM").dblclick()
            page1.get_by_role("button", name="Close").click()
            page1.close()
            return True, f"Success"

        except Exception as e:
            print(f"❌ Error: {e}")
            return False, f"Withdrawal failed"

        finally:
            context.close()
            browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)