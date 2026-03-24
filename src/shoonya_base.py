import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from Base import *

# ────────────────────────────────────────────────
#  CONFIG - CHANGE THESE
# ────────────────────────────────────────────────
USER_ID     = "FN187637"                  # Your Client Code
PASSWORD    = "RamRate$1"

HEADLESS    = False                      # Set True later; False = see browser for debugging

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=300)  # slow_mo helps see actions
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            bypass_csp=True,
        )
        page = await context.new_page()

        try:
            print("Navigating to Kotak...")
            await page.goto("https://trade.shoonya.com/#/", wait_until="networkidle", timeout=45000)

            # Wait for form to appear (page is JS-heavy)
            await page.wait_for_load_state("domcontentloaded")

            # ─── USER ID ─────────────────────────────────────────────
            print("Filling User ID...")
            time.sleep(3)
            await page.keyboard.type(USER_ID, delay=200)
            time.sleep(1)

            await page.keyboard.press('Tab')
            # ─── PASSWORD ────────────────────────────────────────────
            print("Filling Password...")
            time.sleep(1)
            await page.keyboard.type(PASSWORD, delay=200)
            time.sleep(1)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Enter')
            time.sleep(2)
            EMAIL_USR = "prakharvasishtha9@gmail.com"
            EMAIL_PSS = "qmtm daun rljp wjrx"
            sub1 = '(SUBJECT "OTP Generated" UNSEEN)'
            otp1 = otp_shoonya(EMAIL_USR, EMAIL_PSS, sub1)
            print("OTP 1:", otp1)
            time.sleep(1)
            await page.keyboard.press("Shift+Tab")
            time.sleep(.5)
            await page.keyboard.press('Enter')
            time.sleep(1)
            await page.keyboard.press("Shift+Tab")
            time.sleep(.5)
            await page.keyboard.press("Shift+Tab")
            time.sleep(1)
            await page.keyboard.type(otp1, delay=100)

            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Enter')
            time.sleep(2)


            await page.mouse.click(646, 539)
            time.sleep(1)
            await page.mouse.click(725, 610)
            time.sleep(2)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Tab')
            time.sleep(1)
            await page.keyboard.press('Enter')
            time.sleep(1)



            await page.mouse.click(915, 87)
            time.sleep(1)
            await page.mouse.click(540, 239)
            time.sleep(1)
            await page.mouse.click(770, 425)
            time.sleep(1)



            amount = "3"
            await page.mouse.click(838, 86)
            time.sleep(1)
            await page.mouse.click(460, 232)
            time.sleep(1)
            await page.keyboard.type(amount, delay=100)
            time.sleep(1)
            await page.mouse.click(640, 421)
            time.sleep(1)






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

# Run the async function
asyncio.run(main())