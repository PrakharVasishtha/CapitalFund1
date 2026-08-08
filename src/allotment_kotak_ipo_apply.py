import asyncio
import time
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from Base import get_netbanking_otp, load_credentials
import difflib
from common_foundation import logger


def calculate_lot_minimum_hni(min_shares_str: str, higher_price_str: str, type_ipo: str):
    if type_ipo == "mb":
        try:

            min_shares = int(min_shares_str.replace(',', '').strip())
            higher_price = float(higher_price_str.replace('₹', '').replace(',', '').strip())
            lot_value = min_shares * higher_price
            import math
            lots_needed = math.ceil(200001 / lot_value)
            total_shares = lots_needed * min_shares
            return total_shares

        except Exception as e:
            print(f"Error calculating HNI amount: {e}")
            return None

    elif type_ipo == "sme":
        try:
            min_shares = int(min_shares_str.replace(',', '').strip())
            total_shares = (min_shares*3/2)
            return str(total_shares)

        except Exception as e:
            print(f"Error calculating HNI amount: {e}")
            return None
    return None

def calculate_lot_minimum_retail(min_shares_str: str, higher_price_str: str, type_ipo: str):
    try:
        total_shares = min_shares_str
        return str(total_shares)

    except Exception as e:
        print(f"calculate_lot_minimum_retail: {e}")
        return None


async def apply_to_ipo(
    ipo_name="Highness Microelectronics fsafewqgdfvdf",
    USER_ID="jhkh",
    PASSWORD="hkhk",
    EMAIL_USR="prakhar@gmail.com",
    EMAIL_PSS= "fds",
    type_ipo="nn"
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)  # slow_mo helps see actions
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            bypass_csp=True,
        )
        page = await context.new_page()
        #for logger purposes
        filename = USER_ID + "ipoapplied.txt"
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
            await page.keyboard.type(PASSWORD, delay=200)



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
            time.sleep(6)
            #EMAIL_USR = "prakharvasishtha9@gmail.com"
            #EMAIL_PSS = "qmtm daun rljp wjrx"
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
                await page.get_by_text("Investments").click()
                time.sleep(1)

                await page.get_by_text("IPO (ASBA)", exact = True).click()
                time.sleep(1)

                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"appmenu\"]").content_frame.get_by_role("link", name="Apply Now").click()
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#selBeneficiary").select_option("0")
                time.sleep(1)

                print(f"Trying to select IPO: {ipo_name}")

                company_select = page.locator("iframe[name=\"knb2ContainerFrame\"]") \
                    .content_frame.locator("frame[name=\"contentmenu\"]") \
                    .content_frame.locator("#selCompany")

                await company_select.wait_for(state="visible", timeout=10000)

                desired_lower = ipo_name.lower().strip()

                best_match = None
                best_score = -1
                best_index = -1
                best_text = ""

                # Get all options
                options = await company_select.evaluate("""select => {
                    return Array.from(select.options).map((opt, idx) => ({
                        index: idx,
                        value: opt.value,
                        text: opt.textContent.trim()
                    }));
                }""")

                print(f"\nFound {len(options)} IPO options in dropdown.")

                for opt in options:
                    if not opt['text']:
                        continue

                    option_text_lower = opt['text'].lower().strip()

                    # Calculate similarity (better method)
                    similarity = difflib.SequenceMatcher(None, desired_lower, option_text_lower).ratio()

                    #print(f"Option {opt['index']:2d}: {opt['text'][:60]:60} | Score: {similarity:.4f}")

                    if similarity > best_score:
                        best_score = similarity
                        best_index = opt['index']
                        best_text = opt['text']
                        best_match = opt

                # Select the best match
                if best_match and best_score > 0.55:  # adjustable threshold
                    print(f"\n✅ Best match found: '{best_text}'")
                    print(f"   Similarity Score: {best_score:.4f}")

                    await company_select.select_option(value=str(best_index-1))
                    await page.keyboard.press('ArrowDown')
                    await page.keyboard.press('ArrowUp')
                    print(f"   Selected option index: {best_index}")

                    # Verify selection
                    selected_text = await company_select.evaluate(
                        "sel => sel.options[sel.selectedIndex].textContent.trim()"
                    )
                    print(f"   Verified selected text: {selected_text}")
                else:
                    print(f"\n❌ No good match found. Best score was only {best_score:.4f}")
                    # You can add fallback logic here if needed
                    return "IPO selection failed - no good match"
                    
                #Selecting Investor Category
                category_select = page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#invCat")
                print(type_ipo)
                if type_ipo == "mb":
                    category = "individual hni more than rs 2 lakh"
                elif type_ipo == "sme":
                    category = "individual hni more than rs 2 lakh"

                desired_category = category[:25]

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
                    print(f"desired_category  = {desired_category}")
                    
                    
                    similarity = sum(a == b for a, b in zip(desired_category, selected_text)) / max(len(desired_lower), len(selected_text))
                    print(f"Similarity = {similarity}")
                    if similarity > 0.6:
                        print("✅ Successfully selected the correct category!")
                        print(f"   Matched text: {selected_text}")
                        found = True
                        break

                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
                time.sleep(1)

                content_frame = (page.locator("iframe[name=\"knb2ContainerFrame\"]")
                                 .content_frame.locator("frame[name=\"contentmenu\"]")
                                 .content_frame)

                print("\n🔍 Extracting IPO details...")

                min_shares = "Not found"
                higher_price = "Not found"

                try:
                    all_cells = await content_frame.locator("td").all_inner_texts()
                    for i, text in enumerate(all_cells):
                        if "min. no. of shares" in text.lower():
                            if i + 1 < len(all_cells):
                                min_shares = all_cells[i + 1].strip()
                                print(f"✅ Min. No. of Shares (fallback): {min_shares}")
                            break

                except Exception as e1:
                    print(f"Method 1 for Min Shares failed: {e1}")
                    pass

                try:
                    # Higher Price Band
                    all_cells = await content_frame.locator("td").all_inner_texts()
                    for i, text in enumerate(all_cells):
                        if "higher price band" in text.lower() or "upper price" in text.lower():
                            if i + 1 < len(all_cells):
                                higher_price = all_cells[i + 1].strip()
                                print(f"✅ Higher Price Band (fallback): {higher_price}")
                            break

                except Exception as e2:
                    print(f"Method 2 for Price Band failed: {e2}")
                    pass


                print(f"\nFinal Extracted → Min Shares: {min_shares} | Higher Price: {higher_price}")

                total_shares= calculate_lot_minimum_hni(min_shares, higher_price, type_ipo)
                print("total_shares",total_shares)
                if total_shares:
                    # Now fill in your IPO form
                    await content_frame.locator("input[name=\"txtSharesIPO0\"]").fill(str(total_shares))
                    await content_frame.locator("input[name=\"txtPriceIPO0\"]").fill(str(int(higher_price)))

                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtSharesIPO0\"]").press("Tab")
                time.sleep(1)

                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtPriceIPO0\"]").press("Tab")
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.locator("#checkTncId").check()
                time.sleep(1)
                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()

                await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Confirm & Submit").click()

                t1 = await  page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("heading",
                                                                             name="Error in IPO Apply").all_inner_texts()
                t2 = await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_role("heading", name="ERROR",
                                                                             exact=True).all_inner_texts()
                t3 = await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                    "frame[name=\"contentmenu\"]").content_frame.get_by_text("Error Message").all_inner_texts()

                #print(t1, t2, t3)
                time.sleep(1)
                if "error" in t1[0].lower() or "error" in t2[0].lower() or "error" in t3[0].lower():
                    print("applying now in retail category")
                    try:
                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"appmenu\"]").content_frame.get_by_role("link", name="Apply Now").click()
                        time.sleep(1)
                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.locator("#selBeneficiary").select_option("0")
                        time.sleep(1)

                        # Selecting company
                        print(f"Trying to select IPO: {ipo_name}")

                        # Get the company dropdown
                        company_select = page.locator("iframe[name=\"knb2ContainerFrame\"]") \
                            .content_frame.locator("frame[name=\"contentmenu\"]") \
                            .content_frame.locator("#selCompany")

                        await company_select.wait_for(state="visible", timeout=10000)

                        desired_lower = ipo_name.lower().strip()

                        best_match = None
                        best_score = -1
                        best_index = -1
                        best_text = ""

                        # Get all options
                        options = await company_select.evaluate("""select => {
                            return Array.from(select.options).map((opt, idx) => ({
                                index: idx,
                                value: opt.value,
                                text: opt.textContent.trim()
                            }));
                        }""")

                        print(f"\nFound {len(options)} IPO options in dropdown.")

                        for opt in options:
                            if not opt['text']:
                                continue

                            option_text_lower = opt['text'].lower().strip()

                            # Calculate similarity (better method)
                            similarity = difflib.SequenceMatcher(None, desired_lower, option_text_lower).ratio()

                            #print(f"Option {opt['index']:2d}: {opt['text'][:60]:60} | Score: {similarity:.4f}")

                            if similarity > best_score:
                                best_score = similarity
                                best_index = opt['index']
                                best_text = opt['text']
                                best_match = opt

                        # Select the best match
                        if best_match and best_score > 0.55:  # adjustable threshold
                            print(f"\n✅ Best match found: '{best_text}'")
                            print(f"   Similarity Score: {best_score:.4f}")

                            await company_select.select_option(value=str(best_index - 1))
                            await page.keyboard.press('ArrowDown')
                            await page.keyboard.press('ArrowUp')
                            print(f"   Selected option index: {best_index}")

                            # Verify selection
                            selected_text = await company_select.evaluate(
                                "sel => sel.options[sel.selectedIndex].textContent.trim()"
                            )
                            print(f"   Verified selected text: {selected_text}")
                        else:
                            print(f"\n❌ No good match found. Best score was only {best_score:.4f}")
                            # You can add fallback logic here if needed
                            return "IPO selection failed - no good match"

                        # Selecting Investor Category
                        category_select = page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.locator("#invCat")
                        #print(type_ipo)
                        if type_ipo == "mb":
                            category = "retail investor"
                        elif type_ipo == "sme":
                            category = "retail investor                                                  "

                        desired_category = category[:25]

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
                            print(f"desired_category  = {desired_category}")

                            similarity = sum(a == b for a, b in zip(desired_category, selected_text)) / max(
                                len(desired_lower), len(selected_text))
                            print(f"Similarity = {similarity}")
                            if similarity > 0.6:
                                print("✅ Successfully selected the correct category!")
                                print(f"   Matched text: {selected_text}")
                                found = True
                                break

                        time.sleep(1)
                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()
                        time.sleep(1)

                        content_frame = (page.locator("iframe[name=\"knb2ContainerFrame\"]")
                                         .content_frame.locator("frame[name=\"contentmenu\"]")
                                         .content_frame)

                        print("\n🔍 Extracting IPO details...")

                        min_shares = "Not found"
                        higher_price = "Not found"

                        try:
                            all_cells = await content_frame.locator("td").all_inner_texts()
                            for i, text in enumerate(all_cells):
                                if "min. no. of shares" in text.lower():
                                    if i + 1 < len(all_cells):
                                        min_shares = all_cells[i + 1].strip()
                                        #print(f"✅ Min. No. of Shares (fallback): {min_shares}")
                                    break

                        except Exception as e1:
                            #print(f"Method 1 for Min Shares failed: {e1}")
                            pass

                        try:
                            # Higher Price Band
                            all_cells = await content_frame.locator("td").all_inner_texts()
                            for i, text in enumerate(all_cells):
                                if "higher price band" in text.lower() or "upper price" in text.lower():
                                    if i + 1 < len(all_cells):
                                        higher_price = all_cells[i + 1].strip()
                                        #print(f"✅ Higher Price Band (fallback): {higher_price}")
                                    break

                        except Exception as e2:
                            print(f"Method 2 for Price Band failed: {e2}")
                            pass

                        #print(f"\nFinal Extracted → Min Shares: {min_shares} | Higher Price: {higher_price}")

                        total_shares = calculate_lot_minimum_retail(min_shares, higher_price, type_ipo)

                        if total_shares:
                            # Now fill in your IPO form
                            await content_frame.locator("input[name=\"txtSharesIPO0\"]").fill(str(total_shares))
                            await content_frame.locator("input[name=\"txtPriceIPO0\"]").fill(str(int(higher_price)))

                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtSharesIPO0\"]").press(
                            "Tab")
                        time.sleep(1)

                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.locator("input[name=\"txtPriceIPO0\"]").press(
                            "Tab")
                        time.sleep(1)
                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.locator("#checkTncId").check()
                        time.sleep(1)
                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.get_by_role("link", name="Next").click()

                        await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.get_by_role("link",
                                                                                     name="Confirm & Submit").click()
                        st1 = await  page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.get_by_role("heading",
                                                                             name="Error in IPO Apply").all_inner_texts()
                        st2 = await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.get_by_role("heading", name="ERROR",
                                                                             exact=True).all_inner_texts()
                        st3 = await page.locator("iframe[name=\"knb2ContainerFrame\"]").content_frame.locator(
                            "frame[name=\"contentmenu\"]").content_frame.get_by_text("Error Message").all_inner_texts()
                        
                        if "error" in t1[0].lower() or "error" in t2[0].lower() or "error" in t3[0].lower():
                            print("Error in 2nd round")
                            return None

                        logger(filename,"applied in retail",ipo_name)
                            
                        time.sleep(1)
                        return None

                    except Exception as e:
                        print(f"\nERROR: {str(e)}")
                        time.sleep(1)
                        return "Not Applied"

                else:
                    print("No error text")
                    logger(filename,"applied in SNI",ipo_name)
                    return None

            except Exception as e:
                print(f"\nERROR: {str(e)}")
                await page.screenshot(path="kotak-ipo-error.png")
                print("Screenshot saved: kotak-ipo-error.png")
                time.sleep(1)

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="error-screenshot.png")
            print("Error screenshot saved.")
            return "Error in Applying"
        time.sleep(1)

        await context.close()
        await browser.close()

def apply_to_ipo_all_users(ipo_name="ipo hsgserratergadg", type_ipo="sme"):
    credentials_file = "credentials.json"
    users = load_credentials(credentials_file)
    # Users
    for user in users:
        uci = user.get("uci")
        bank_user = user.get("bank_user")
        bank_password = user.get("bank_password")
        email_user = user.get("email_user")
        email_password = user.get("email_password")

        result = asyncio.run(apply_to_ipo(ipo_name=ipo_name,USER_ID=bank_user,PASSWORD=bank_password,EMAIL_USR=email_user,EMAIL_PSS= email_password,type_ipo=type_ipo))
        print("IPO",ipo_name,"result:",result)
        file_path=uci+".txt"
        logger(file_path,ipo_name,result)

# Run the async function
#asyncio.run(apply_to_ipo())
#apply_to_ipo_all_users(ipo_name="Citius Transnet", type_ipo="mb")
#apply_to_ipo_all_users(ipo_name="Mehul Telecom", type_ipo="sme")
