import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from Base import *
import difflib


# ────────────────────────────────────────────────
#  CONFIG - CHANGE THESE
# ────────────────────────────────────────────────
USER_ID     = "961633451"                  # Your Client Code
PASSWORD    = "RamRate#26"

HEADLESS    = False                      # Set True later; False = see browser for debugging
DESIRED_IPO_NAME = "Highness Microelectronics"



async def apply_to_ipo(
    ipo_name="Highness Microelectronics",
    bank_user="jhkh",
    bank_pwd="hkhk",
    type="MB",
    headless=False
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=300)  # slow_mo helps see actions
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            bypass_csp=True,
        )
        page = await context.new_page()

        try:
            print("Navigating to Kotak...")
            await page.goto("https://netbanking.kotak.bank.in/knb2/", wait_until="networkidle", timeout=45000)

            # Wait for form to appear (page is JS-heavy)
            await page.wait_for_load_state("domcontentloaded")

            # ─── USER ID ─────────────────────────────────────────────
            print("Filling User ID...")
            user_locator = page.locator(
                'input[placeholder*="User"][type="text"], '
                'input[placeholder*="Client"], '
                'input[placeholder*="ID"], '
                '[aria-label*="user" i], '
                'input[name*="user" i], '
                'input[id*="user" i]'
            ).first

            await user_locator.wait_for(state="visible", timeout=10000)
            await user_locator.fill(USER_ID)
            time.sleep(1)
            await page.keyboard.press('Tab')
            # ─── PASSWORD ────────────────────────────────────────────
            print("Filling Password...")
            await page.keyboard.type("RamRate#26", delay=200)



            # ─── LOGIN BUTTON ────────────────────────────────────────
            print("Clicking Login...")
            login_button = page.locator(
                'button:has-text("Login"), '
                'button:has-text("Sign In"), '
                'button[type="submit"], '
                'button[class*="login" i], '
                '[role="button"]:has-text("Login")'
            ).first

            await login_button.click()
            time.sleep(9)
            EMAIL_USR = "prakharvasishtha9@gmail.com"
            EMAIL_PSS = "qmtm daun rljp wjrx"
            sub1 = '(SUBJECT "Net Banking login" UNSEEN)'
            otp1 = get_netbanking_otp(EMAIL_USR, EMAIL_PSS, sub1)
            print("OTP 1:", otp1)
            time.sleep(1)
            await page.keyboard.type(otp1, delay=100)

            # ─── LOGIN BUTTON ────────────────────────────────────────
            print("Clicking Login...")
            login_button = page.locator(
                'button:has-text("Login"), '
                'button:has-text("Sign In"), '
                'button[type="submit"], '
                'button[class*="login" i], '
                '[role="button"]:has-text("Login")'
            ).first

            await login_button.click()

            try:
                # 1. Click on 'Investments' from the top menu
                # We use a filter to ensure we get the main menu link
                await page.get_by_text("Investments").click()
                time.sleep(1)
                # 2. Click on 'IPO (ASBA)'
                # Note: In some versions of Kotak, this might be under a 'More' tab
                # or directly visible after clicking Investments.
                await page.get_by_text("IPO (ASBA)", exact = True).click()
                time.sleep(1)
                # 3. Click on 'Apply Now'
                # This usually appears on the left sidebar or as a primary button on the ASBA page.

                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"appmenu\"]").content_frame.get_by_role("link", name="Apply Now").click()
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#selBeneficiary").select_option("0")
                time.sleep(1)
                print(f"Trying to select IPO: {DESIRED_IPO_NAME}")
                
                #Selecting company
                company_select = page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#selCompany")


                desired_lower = DESIRED_IPO_NAME.lower()
                desired_lower = desired_lower.lower()[:25]

                for i in range(25):
                    await company_select.select_option(value=str(i))

                    selected_value = await company_select.input_value()
                    selected_text = await company_select.evaluate(
                        "sel => sel.options[sel.selectedIndex].textContent.trim()",
                        arg=company_select
                    )
                    selected_text = selected_text.lower()[:25]

                    print("\nVerification:")
                    print(f"Selected value = {selected_value}")
                    print(f"Selected text  = {selected_text}")
                    print(f"Desired text  = {desired_lower}")
                    
                    similarity = sum(a == b for a, b in zip(desired_lower, selected_text)) / max(len(desired_lower), len(selected_text))
                    print(f"Similarity = {similarity}")
                    if similarity > 0.75:
                        print("✅ Successfully selected the correct IPO!")
                        print(f"   Matched text: {selected_text}")
                        found = True
                        break
                    
                #Selecting Investor Category
                category_select = page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#invCat")


                category = "high networth individual"
                desired_category = cat[:25]

                for i in range(7):
                    await category_select.select_option(value=str(i))

                    selected_value = await category_select.input_value()
                    selected_text = await category_select.evaluate(
                        "sel => sel.options[sel.selectedIndex].textContent.trim()",
                        arg=category_select
                    )
                    selected_text = selected_text.lower()[:25]

                    print("\nVerification:")
                    print(f"Selected value = {selected_value}")
                    print(f"Selected text  = {selected_text}")
                    print(f"Desired text  = {desired_category}")
                    
                    
                    similarity = sum(a == b for a, b in zip(desired_category, selected_text)) / max(len(desired_lower), len(selected_text))
                    print(f"Similarity = {similarity}")
                    if similarity > 0.75:
                        print("✅ Successfully selected the correct category!")
                        print(f"   Matched text: {selected_text}")
                        found = True
                        break

               # await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    #"frame[name=\"contentmenu\"]").content_frame.locator("#invCat")
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtSharesIPO0\"]").click()
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtSharesIPO0\"]").fill("2400")
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtSharesIPO0\"]").press("Tab")
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtPriceIPO0\"]").fill("117")
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtPriceIPO0\"]").press("Tab")
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#checkTncId").check()
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
                time.sleep(1)


                # You can continue from here (enter bid amount, quantity, etc.)

            except Exception as e:
                print(f"\nERROR: {str(e)}")
                await page.screenshot(path="kotak-ipo-error.png")
                print("Screenshot saved: kotak-ipo-error.png")
                time.sleep(1)




            except Exception as e:
                print(f"Error: {e}")

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
asyncio.run(apply_to_ipo())