import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://netbanking.kotak.bank.in/knb2/")
    page.get_by_role("textbox", name="CRN, Username or Card Number").fill("961633451RamRate#26")
    page.get_by_role("textbox", name="Password").click(modifiers=["ControlOrMeta"])
    page.get_by_role("textbox", name="Password").click(modifiers=["ControlOrMeta"])
    page.get_by_role("textbox", name="CRN, Username or Card Number").click()
    page.get_by_role("textbox", name="CRN, Username or Card Number").fill("961633451")
    page.get_by_role("textbox", name="Enter Captcha").click()
    page.get_by_role("textbox", name="Password").click(modifiers=["ControlOrMeta"])
    page.get_by_role("button", name="Secure login").click()
    page.get_by_role("textbox", name="otpMobile").fill("894836")
    page.get_by_role("button", name="Secure login").click()
    page.get_by_text("Apply now").click()
    page.get_by_text("Investments").click()
    page.get_by_text("IPO (ASBA)", exact=True).click()

    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#checkTncId").check()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Confirm & Submit").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
