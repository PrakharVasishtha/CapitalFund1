import re
from playwright.sync_api import Playwright, sync_playwright, expect
import pyotp

# ────────────────────────────────────────────────
#  CONFIG - CHANGE THESE
# ────────────────────────────────────────────────
USER_ID     = "MFB802"                  # Your Client Code
PASSWORD    = "RamRate$1"
secret = "DOIIMB2PTIIOCKDQ4ILOCPVF44YJ7QBU"
HEADLESS    = False                      # Set True later; False = see browser for debugging



def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kite.zerodha.com/")
    page.get_by_role("textbox", name="Phone number or User ID").click()
    page.get_by_role("textbox", name="Phone number or User ID").fill("MFB802")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill("RamRate$1")
    page.get_by_role("button", name="Login").click()
    totp = pyotp.TOTP(secret)
    current_otp = totp.now()
    page.get_by_role("spinbutton", name="External TOTP").click()
    page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)
    page.get_by_role("link", name="Funds").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="Withdraw").click()
    page1 = page1_info.value
    page1.close()
    with page.expect_popup() as page2_info:
        page.get_by_role("link", name="Withdraw").click()
    page2 = page2_info.value
    page2.goto("https://console.zerodha.com/funds/overview?src=kiteweb")
    page2.locator("#eq_input").click()
    page2.locator("#eq_input").click()
    page2.locator("#eq_input").fill("5")
    page2.get_by_role("button", name="Continue").click()
    page2.get_by_role("button", name="Confirm").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
