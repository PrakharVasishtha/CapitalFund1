import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kite.zerodha.com/")
    page.get_by_role("textbox", name="Phone number or User ID").fill("MFB802")
    page.get_by_role("textbox", name="Phone number or User ID").press("Tab")
    page.get_by_role("textbox", name="Password").fill("RamRate$1")
    page.get_by_role("button", name="Login").click()
    page.get_by_role("spinbutton", name="External TOTP").fill("016319")
    page.get_by_role("link", name="Holdings").click()
    page.get_by_role("cell", name="NIFTYIETF").click()
    page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").click()
    page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").click()
    page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").click()
    page.get_by_role("button", name="Cancel").click()
    page.get_by_text("T1:").click()
    page.get_by_role("columnheader", name=" Qty.").click()
    page.get_by_text("Qty.").click()
    page.get_by_role("button", name="Sell").click()
    page.get_by_role("button", name="Cancel").click()
    page.get_by_role("link", name="Holdings").click()
    page.get_by_role("link", name="NIFTYIETF").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
