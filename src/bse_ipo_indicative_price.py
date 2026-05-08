import re
import time
from playwright.sync_api import Playwright, sync_playwright, expect

def ipo_indicative_price_bse(
        ipo_name: str,
        exchange: str,
        timeout: int = 5000,
) -> tuple[bool, str]:
    def run(playwright: Playwright) -> None:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.bseindia.com/")
        page.get_by_role("button", name="Close").click()
        page.get_by_role("textbox", name="smart search").click()
        page.get_by_role("textbox", name="smart search").click()
        page.get_by_role("textbox", name="smart search").fill("Mehul Telecom")
        time.sleep(2)
        page.get_by_role("textbox", name="smart search").press("ArrowDown")
        page.get_by_role("textbox", name="smart search").press("Enter")
        time.sleep(2)
        try:
            x = page.locator("#idcrval").inner_text()
        except Exception as e:
            print(e)
            
        print(x)
        return float(x)
        # ---------------------
        context.close()
        browser.close()


    with sync_playwright() as playwright:
    run(playwright)
