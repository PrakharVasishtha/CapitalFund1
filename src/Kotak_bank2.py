import asyncio
import time
from Base import *
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
# from Base import *   # assuming this contains get_netbanking_otp()

# ────────────────────────────────────────────────
#  CONFIG - CHANGE THESE
# ────────────────────────────────────────────────
USER_ID     = "961633451"                  # Your Client Code
PASSWORD    = "RamRate#26"
EMAIL_USR   = "prakharvasishtha9@gmail.com"
EMAIL_PSS   = "qmtm daun rljp wjrx"

# ─── CHANGE THIS TO THE IPO YOU WANT ────────────────────────────────
DESIRED_IPO_NAME = "Acetech E-Commerce"          # ←←← Put exact company name here
# DESIRED_IPO_NAME = "Bajaj Housing Finance"
# DESIRED_IPO_NAME = "Swiggy"   etc.

HEADLESS = False

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=400)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            bypass_csp=True,
        )
        page = await context.new_page()

        try:
            print("Navigating to Kotak Netbanking...")
            await page.goto("https://netbanking.kotak.bank.in/knb2/", wait_until="networkidle", timeout=60000)

            time.sleep(2)
            # ─── LOGIN ─────────────────────────────────────────────────────
            print("Filling User ID...")
            await page.fill('input[placeholder*="User"], input[placeholder*="Client"], input[name*="user" i]', USER_ID)
            await page.keyboard.press("Tab")

            print("Filling Password...")
            await page.keyboard.type(PASSWORD, delay=80)

            print("Clicking Login...")
            await page.locator('button:has-text("Login"), button[type="submit"], [role="button"]:has-text("Login")').click()

            # Wait for OTP email and enter OTP
            time.sleep(6)  # give time for email to arrive
            sub1 = '(SUBJECT "Net Banking login" UNSEEN)'
            otp = get_netbanking_otp(EMAIL_USR, EMAIL_PSS, sub1)   # your function
            print(f"OTP received: {otp}")

            if not otp or len(otp) < 4:
                raise ValueError("Could not retrieve valid OTP")

            await page.keyboard.type(otp, delay=100)

            print("Submitting OTP...")
            await page.locator('button:has-text("Login"), button[type="submit"]').click()

            await page.wait_for_load_state("networkidle", timeout=45000)

            # ─── Navigate to IPO ASBA ──────────────────────────────────────
            print("Clicking 'Investments'...")
            await page.get_by_text("Investments", exact=False).click(delay=200)
            await asyncio.sleep(1.5)

            print("Clicking 'IPO (ASBA)'...")
            await page.get_by_text("IPO (ASBA)", exact=True).click()
            await asyncio.sleep(2)

            # Most reliable way: work inside the correct iframe combination
            main_frame = page.frame_locator('iframe[name="knb2ContainerFrame"]')
            app_frame = main_frame.frame_locator('frame[name="appmenu"]')
            content_frame = main_frame.frame_locator('frame[name="contentmenu"]')

            print("Clicking 'Apply Now'...")
            await app_frame.get_by_role("link", name="Apply Now").click()
            await asyncio.sleep(2.5)

            # ─── Select Beneficiary (usually first one) ────────────────────
            print("Selecting primary beneficiary...")
            await content_frame.locator("#selBeneficiary").select_option("0")
            await asyncio.sleep(1)

            # ─── Select Company by visible text ────────────────────────────
            print(f"Trying to select IPO: {DESIRED_IPO_NAME}")

            company_select = content_frame.locator("#selCompany")

            # Wait until the dropdown has options
            await company_select.click()

            # Get all available options for debugging
            options = await company_select.evaluate("""select => {
                return Array.from(select.options).map(opt => ({
                    value: opt.value,
                    text: opt.textContent.trim()
                }));
            }""")


            # ─── VERIFICATION ──────────────────────────────────────────────
            await asyncio.sleep(1.2)

            selected_value = await company_select.input_value()
            selected_text = await company_select.evaluate(
                "sel => sel.options[sel.selectedIndex].textContent.trim()",
                arg=company_select
            )

            print("\nVerification:")
            print(f"Selected value = {selected_value}")
            print(f"Selected text  = {selected_text}")


        except Exception as e:
            print(f"\nERROR: {str(e)}")
            await page.screenshot(path="kotak-ipo-error.png")
            print("Screenshot saved: kotak-ipo-error.png")

        finally:
            if not HEADLESS:
                print("\nBrowser will remain open for 90 seconds for inspection...")
                await asyncio.sleep(90)
            # await context.close()
            # await browser.close()

if __name__ == "__main__":
    asyncio.run(main())