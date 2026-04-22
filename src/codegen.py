import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kite.zerodha.com/")


    page.get_by_text("NIFTYIETF").click()
    page.get_by_role("button", name="Buy").click()
    page.get_by_text("Regular").click()

    page.locator("label").first.click()
    page.locator("label").first.click()
    page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").click()
    page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").fill("12")
    page.get_by_role("button", name="Buy").click()
    page.locator(".icon.icon-times.close").click()
    page.get_by_role("button", name="Cancel").click()


    page.get_by_role("textbox", name="Search eg: infy bse, nifty").click()
    page.get_by_role("textbox", name="Search eg: infy bse, nifty").fill("")
    page.locator("div").filter(has_text="Hi, Sonam equity 0.1 Margin").nth(3).click()
    page.get_by_role("button", name="Buy").click()
    page.get_by_role("button", name="Buy").click()
    page.locator(".icon.icon-times.close").click()
    page.get_by_role("button", name="Cancel").click()
    page.get_by_role("button", name="Buy").click()
    page.get_by_role("button", name="Buy").click()
    page.get_by_text("Regular").click()
    page.locator(".icon.icon-times").click()
    page.get_by_role("spinbutton", name="Price", exact=True).click()
    page.get_by_role("button", name="Buy").click()
    page.locator(".icon.icon-times").click()
    page.get_by_role("button", name="Cancel").click()
    page.get_by_role("link", name="User profile").click()
    page.get_by_text("equity 0.1 Margin available").click()
    page.get_by_text("0.1 Margin available Margins").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
