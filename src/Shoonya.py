import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from Base import *


sync def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=300)  # slow_mo helps see actions
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            bypass_csp=True,
        )
        page = await context.new_page()

        try:
            print("Navigating to Shoonya...")
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            await page.goto("https://trade.shoonya.com/#/")
            await page.get_by_role("textbox").click()
            await page.get_by_role("textbox").fill("FN187637")
            await page.get_by_role("textbox").click()
            await page.get_by_role("textbox").fill("RamRate$1")
            await page.locator("flt-glass-pane").click()
            await page.get_by_role("textbox").click()
            # page.get_by_role("textbox").fill("24085")
            await page.locator("flt-glass-pane").click()
            await page.locator("iframe").content_frame.locator("html").click()
            await page.locator("iframe").content_frame.get_by_role("button", name="Accept").click()
            await page.locator("flt-platform-view:nth-child(2) > div").click()
            with page.expect_popup() as page1_info:
                page.locator("flt-platform-view:nth-child(2) > div").click()
            page1 = page1_info.value
            page1.get_by_placeholder("1.00").click()
            page1.get_by_placeholder("1.00").fill("1000")
            page1.get_by_role("button", name="Proceed").click()
            page1.get_by_role("button", name="OK").click()
            page1.close()

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="error-screenshot.png")
            print("Error screenshot saved.")

        finally:
            if not HEADLESS:
                # Keep open for inspection
                print("Browser will stay open for 60 seconds...")
                await asyncio.sleep(60)
            #await context.close()
            #await browser.close()

asyncio.run(main())