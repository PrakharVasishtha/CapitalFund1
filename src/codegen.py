import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kite.zerodha.com/")
    page.get_by_role("textbox", name="Phone number or User ID").click()
    page.get_by_role("textbox", name="Phone number or User ID").fill("MFB802")
    page.get_by_role("textbox", name="Phone number or User ID").press("Tab")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill("RamRate$1")
    page.get_by_role("button", name="Login").click()
    page.get_by_role("spinbutton", name="External TOTP").click()
    page.get_by_role("spinbutton", name="External TOTP").fill("852499")
    page.get_by_role("link", name="Funds").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="Withdraw").click()
    page1 = page1_info.value
    page1.get_by_text("₹").nth(5).click()
    page1.locator("#equity_card").get_by_text("Withdrawable balance").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
