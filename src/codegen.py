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
    page.get_by_role("spinbutton", name="External TOTP").fill("653885")
    page.get_by_role("link", name="Funds").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("button", name="Add funds").click()
    page1 = page1_info.value
    page1.get_by_role("textbox", name="Enter amount").fill("700")
    page1.get_by_text("Net banking₹9 + GST").click()
    page1.get_by_role("button", name="Continue").click()
    page1.get_by_role("link", name="CRN").click()
    page1.get_by_role("tabpanel", name="CRN").get_by_placeholder("Enter CRN or Customer ID").click()
    page1.get_by_role("tabpanel", name="CRN").get_by_placeholder("Enter CRN or Customer ID").click()
    page1.get_by_role("tabpanel", name="CRN").get_by_placeholder("Enter CRN or Customer ID").fill("961633451")
    page1.get_by_role("tabpanel", name="CRN").get_by_placeholder("Enter CRN or Customer ID").press("Tab")
    page1.get_by_role("textbox", name="Select Bank Select Bank").fill("RamRate#26")
    page1.get_by_role("link", name="SECURE LOGIN").click()
    page1.locator("#dynamic-access").click()
    page1.locator("#dynamic-access").click()
    page1.locator("#dynamic-access").click()
    page1.locator("#dynamic-access").fill("398523")
    page1.get_by_role("link", name="Verify").click()
    page1.get_by_role("link", name="CONFIRM").dblclick()
    page1.get_by_role("button", name="Close").click()
    page1.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
