import asyncio
import time
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from logger_setup import get_logger

logger = get_logger(__name__)


async def get_kotak_balance(
    USER_ID="jhkh",
    PASSWORD="hkhk",
    EMAIL_USR="prakhar@gmail.com",
    EMAIL_PSS= "fds"):

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            logger.info(f"Navigating to Kotak Net Banking for User {USER_ID}...")
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

            from Base import get_netbanking_otp
            otp1 = get_netbanking_otp(EMAIL_USR, EMAIL_PSS, sub1)
            logger.info(f"OTP received for Kotak login: {bool(otp1)}")
            if not otp1:
                logger.error("OTP not received for Kotak login")
                return 0

            await page.get_by_role("textbox", name=re.compile("otp|OTP", re.I)).fill(str(otp1))
            await page.get_by_role("button", name=re.compile("Secure login|Login", re.I)).click()

            # Wait for dashboard to fully load
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # ─── Extract Balance ─────────────────────────────
            logger.info("Extracting Kotak balance from dashboard...")
            balance_texts = []

            try:
                await page.get_by_text("View balance", exact=False).first.click()
                await page.wait_for_timeout(2000)
                b4 = await page.locator("text=₹").first.inner_text()
                balance_texts.append(b4.strip())
            except Exception:
                pass

            if balance_texts:
                raw = balance_texts[0]
                cleaned = re.sub(r'[^\d.]', '', raw.replace(',', ''))
                try:
                    balance = int(float(cleaned))
                    logger.info(f"Parsed Kotak Balance for {USER_ID}: ₹{balance}")
                    return balance
                except Exception:
                    logger.warning(f"Could not parse raw balance: {raw}")
                    return 0
            else:
                logger.warning("No balance text found on Kotak dashboard.")
                await page.screenshot(path="kotak_balance_not_found.png")
                return 0

        except Exception as e:
            logger.exception(f"Error fetching Kotak balance for {USER_ID}: {e}")
            try:
                await page.screenshot(path="kotak_error.png")
            except Exception:
                pass
            return 0

        finally:
            if 'context' in locals():
                await context.close()
            if 'browser' in locals():
                await browser.close()


# Run the script
#print(asyncio.run(get_kotak_balance(USER_ID=bank_user,PASSWORD=bank_password,EMAIL_USR=email_user,EMAIL_PSS= email_password)))