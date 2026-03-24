import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://netbanking.kotak.bank.in/knb2/")
    page.get_by_role("textbox", name="CRN, Username or Card Number").fill("961633451")
    page.get_by_role("textbox", name="CRN, Username or Card Number").press("Tab")
    page.get_by_role("button", name="Secure login").click()
    page.get_by_role("textbox", name="otpMobile").fill("554240")
    page.get_by_role("button", name="Secure login").click()
    page.locator("app-summary-asset").get_by_text("View balance").click()
    page.get_by_text("Investments").click()
    page.get_by_text("IPO (ASBA)", exact=True).click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"appmenu\"]").content_frame.get_by_role("link", name="Apply Now").click()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#selBeneficiary").select_option("0")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("iframe[name=\"contentmenu\"]").content_frame.locator("#selCompany").select_option("8")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#invCat").select_option("0")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#invCat").select_option("1")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_text("423000").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_text("423000").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_text("423000").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("body").press("Enter")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtSharesIPO0\"]").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtPriceIPO0\"]").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#checkTncId").check()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
