import time
from common_foundation import logger
import openpyxl
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp

def update_excel(uci_target: int, amount_needed: int):
    try:
        from master_excel_manager import update_master_user
        update_master_user(uci=str(uci_target), amount_needed=abs(amount_needed))
        print(f"Successfully updated details for uci_target {uci_target} in Master.xlsx")
    except Exception as e:
        print(f"An error occurred while updating Master.xlsx: {e}")

def withdraw_from_zerodha(
        user_uci: int,
        user_id: str,
        password: str,
        totp_secret: str,
        amount: float | int,
        headless: bool = False,
        timeout: int = 45000,
) -> tuple[bool, str]:

    #amount_str = str(int(float(amount)))  # Zerodha usually wants whole numbers

    def run(playwright: Playwright) -> tuple[bool, str]:
        print(user_id,"reqrd to withdrw frm zerodha",amount)
        amount_str = "0"
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
            still_needed_amount = int(final_amount - amount)
            print("still_needed_amount",still_needed_amount)
            update_excel(uci_target =user_uci, amount_needed = still_needed_amount)
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
                msg_log = "withdrawal initiated on broker"
                print(msg_log)
                # Give some time for confirmation (you can improve this)
                withdraw_page.wait_for_timeout(4000)
            else:
                msg_log = "less than 1 amount, so no withdrawal"
                print(msg_log)
            return True, f"."

        except Exception as e:
            msg_log = e
            print(msg_log)
            import traceback
            return False, f"Withdrawal failed: {str(e)}\n{traceback.format_exc()}"
        

        finally:
            file_path = user_uci + ".txt"
            logger(file_path, amount_str, msg_log)
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)