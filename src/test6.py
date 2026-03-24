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
    page.get_by_role("textbox", name="otpMobile").fill("062078")
    page.get_by_role("button", name="Secure login").click()
    page.get_by_text("Investments").click()
    page.locator("div").filter(has_text=re.compile(r"^IPO \(ASBA\)$")).nth(1).click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"appmenu\"]").content_frame.get_by_role("link", name="Apply Now").click()
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#selBeneficiary").select_option("0")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#selCompany").select_option("3")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#invCat").select_option("0")
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#selCompany").select_option("0")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#selCompany").select_option("14")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_text("Apply Now Beneficiary").click()
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("body").press("AudioVolumeMute")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.locator("#invCat").select_option("0")
    page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator("frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
    page.goto("https://netbanking.kotak.bank.in/knb2/")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
