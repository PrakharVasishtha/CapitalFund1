import asyncio
import time
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def get_kotak_balance(
    USER_ID="jhkh",
    PASSWORD="hkhk",
    EMAIL_USR="prakhar@gmail.com",
    EMAIL_PSS= "fds"):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            print("🚀 Navigating to Kotak Net Banking...")
            await page.goto("https://netbanking.kotak.bank.in/knb2/",
                            wait_until="networkidle", timeout=60000)

            # ─── Login ─────────────────────────────────────
            print("Filling User ID...")
            await page.get_by_role("textbox", name=re.compile("CRN|Username|Card", re.I)).fill(USER_ID)
            await page.keyboard.press("Tab")

            print("Filling Password...")
            await page.get_by_role("textbox", name="Password").fill(PASSWORD)

            print("Clicking Secure Login...")
            await page.get_by_role("button", name=re.compile("Secure login|Login", re.I)).click()

            # OTP handling (you already have email logic)
            time.sleep(8)  # wait for OTP email

            sub1 = '(SUBJECT "Net Banking login" UNSEEN)'

            from Base import get_netbanking_otp  # assuming this exists
            otp1 = get_netbanking_otp(EMAIL_USR, EMAIL_PSS, sub1)
            print("OTP received:", otp1)

            await page.get_by_role("textbox", name=re.compile("otp|OTP", re.I)).fill(otp1)
            await page.get_by_role("button", name=re.compile("Secure login|Login", re.I)).click()

            # Wait for dashboard to fully load
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(3000)  # extra safety

            # ─── Extract Balance ─────────────────────────────
            print("\n🔍 Trying to extract balance...")

            balance_texts = []



            # Method 4: Click on "View balance" / "Accounts" if needed
            try:
                await page.get_by_text("View balance", exact=False).first.click()
                await page.wait_for_timeout(2000)
                b4 = await page.locator("text=₹").first.inner_text()
                balance_texts.append(b4.strip())
            except:
                pass
            print("Balance texts:", balance_texts)
            # ─── Print all found balances ─────────────────────
            print("\n=== BALANCE RESULTS ===")
            for i, txt in enumerate(balance_texts, 1):
                print(f"Found {i}: {txt}")

            # Clean and parse the best one (remove ₹, commas, etc.)
            if balance_texts:
                raw = balance_texts[0]
                # Extract numbers only
                cleaned = re.sub(r'[^\d.]', '', raw.replace(',', ''))
                try:
                    balance = int(float(cleaned))
                    print(f"\n✅ Parsed Balance: ₹ {balance}")
                    return balance
                except:
                    print(f"\nRaw balance (could not parse): {raw}")
                    return 0
            else:
                print("❌ No balance text found. Taking screenshot...")
                await page.screenshot(path="kotak_balance_not_found.png")
                return 0

            # Optional: Navigate to full account overview
            await page.get_by_text("Accounts/Deposits", exact=False).click()
            await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="kotak_error.png")
            print("Screenshot saved: kotak_error.png")


        await context.close()
        await browser.close()
        return 0


# Run the script
#print(asyncio.run(get_kotak_balance(USER_ID=bank_user,PASSWORD=bank_password,EMAIL_USR=email_user,EMAIL_PSS= email_password)))