import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kite.zerodha.com/")
    page.get_by_role("textbox", name="Phone number or User ID").fill("PUT824")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill("RamRate$1")
    page.get_by_role("button", name="Login").click()
    page.get_by_role("spinbutton", name="External TOTP").fill("719322")
    page.get_by_role("button", name="Buy").click()
    page.get_by_text("Regular").click()
    page.get_by_text("Regular").click()
    page.get_by_text("Regular").dblclick()
    page.get_by_text("Regular").click()
    page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").click()
    page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").fill("122")
    page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").press("Tab")
    page.get_by_role("spinbutton", name="Price", exact=True).press("ControlOrMeta+c")
    page.get_by_role("spinbutton", name="Price", exact=True).fill("275")
    page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
    page.get_by_role("button", name="Buy").click()
    page.get_by_role("button", name="Cancel").click()
    page.locator(".icon.icon-times").click()
    page.get_by_role("button", name="Buy").click()
    page.get_by_text("Regular").click()
    page.get_by_role("spinbutton", name="BUY TATAELXSI (NSE) quantity").click()
    page.get_by_role("spinbutton", name="BUY TATAELXSI (NSE) quantity").press("Unidentified")


    page.get_by_role("spinbutton", name="BUY TATAELXSI (NSE) quantity").fill("12225")
    page.get_by_role("spinbutton", name="BUY TATAELXSI (NSE) quantity").press("Tab")
    page.get_by_role("spinbutton", name="Price", exact=True).press("ControlOrMeta+c")
    page.get_by_role("spinbutton", name="Price", exact=True).fill("4678")
    page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
    page.get_by_role("button", name="Buy").click()
    page.locator(".icon.icon-times").click()
    page.get_by_role("link", name="Orders").click()
    page.get_by_role("row", name="08:15:10 BUY TATAELXSI NSE").get_by_role("button").click()
    page.get_by_role("link", name=" Cancel").click()
    page.get_by_role("button", name="Cancel order").click()
    page.get_by_role("button", name="Sell").click()
    page.get_by_role("button", name="Cancel").click()
    page.get_by_role("button", name="Sell").click()
    page.get_by_text("Regular").click()
    page.get_by_role("spinbutton", name="SELL TATAGOLD (NSE) quantity").click()
    page.get_by_role("spinbutton", name="SELL TATAGOLD (NSE) quantity").fill("12")
    page.get_by_role("spinbutton", name="SELL TATAGOLD (NSE) quantity").press("Tab")
    page.get_by_role("spinbutton", name="Price", exact=True).press("ControlOrMeta+c")
    page.get_by_role("spinbutton", name="Price", exact=True).fill("14.69")
    page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
    page.get_by_role("button", name="Sell").click()
    page.get_by_role("button", name="Cancel").click()

    page.get_by_role("link", name="Funds").click()
    page.get_by_role("row", name="Available margin 0.10").get_by_role("heading").click()
    page.get_by_role("cell", name="Available margin").first.click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
