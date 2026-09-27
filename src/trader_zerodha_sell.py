import time
import Base
from common_foundation import logger as legacy_logger
from logger_setup import get_logger
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp

logger = get_logger(__name__)

def zerodha_sell(
        user_id: str,
        password: str,
        totp_secret: str,
        security_symbol: str,
        headless: bool = False,
        timeout: int = 5000,
) -> tuple[bool, str]:
    def run(playwright: Playwright) -> tuple[bool, str]:
        logger.info(f"Initiating Zerodha Sell: User={user_id}, Symbol={security_symbol}")
        try:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                )
            )
            file_path=user_id +".txt"
            amt_symbl = security_symbol
            
            page: Page = context.new_page()
            page.set_default_timeout(timeout)

            # ── Login ───────────────────────────────────────────────
            page.goto("https://kite.zerodha.com/", wait_until="domcontentloaded")
            time.sleep(1)

            page.get_by_role("textbox", name="Phone number or User ID").fill(user_id)
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("button", name="Login").click()
            time.sleep(1)

            # ── TOTP ────────────────────────────────────────────────
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            page.get_by_role("spinbutton", name="External TOTP").fill(current_otp)
            time.sleep(2)
            page.mouse.click(30, 50)
            time.sleep(.5)

            if security_symbol == "NIFTYIETF":
                page.keyboard.press('ArrowDown')
            elif security_symbol == "TATAGOLD":
                page.keyboard.press('ArrowDown')
                time.sleep(.3)
                page.keyboard.press('ArrowDown')
            elif security_symbol == "TATSILV":
                page.keyboard.press('ArrowDown')
                time.sleep(.3)
                page.keyboard.press('ArrowDown')
                time.sleep(.3)
                page.keyboard.press('ArrowDown')
            security_sell = "SELL " + security_symbol + " (NSE) quantity"
            security_sell_nse = "SELL " + security_symbol + " (NSE) quantity"
            security_sell_bse = "SELL " + security_symbol + " (BSE) quantity"
            print(security_sell)
            time.sleep(1)

            time.sleep(1)
            try:
                page.keyboard.press('S')
                page.get_by_text("Regular").click()
                price = page.get_by_role("spinbutton", name="Price", exact=True).input_value()
                page.get_by_role("button", name="Cancel").click()
                p = Base.parse_float(price)
                p1 = str(round(Base.parse_float(p * 1.0005),2))
                p2 = str(round(Base.parse_float(p * 1.0015),2))
                target_prices = [p1, p2]

            except Exception as e:
                print(e)
                
            page.get_by_role("link", name="Holdings").click()
            time.sleep(2)
            try:
                page.get_by_role("cell", name=security_symbol).click()
                page.get_by_role("link", name="NIFTYIETF").click()
                try:
                    holdings = page.get_by_role("spinbutton", name=security_sell_nse).input_value()
                except Exception as e:
                    print(e)
                    holdings = page.get_by_role("spinbutton", name=security_sell_bse).input_value()
                logger.info(f"Holdings found for {security_symbol}: {holdings}")
                page.get_by_role("button", name="Cancel").click()
            except Exception as e:
                holdings = 0
                logger.warning(f"Could not read holdings for {security_symbol}: {e}")
                
            if holdings != 0:
                q = str(int(int(holdings) / 4))
            else:
                q = 0

            logger.info(f"Holdings: {holdings}, Qty per order: {q}, Base price: {p}, Target prices: {target_prices}")
            
            # Place sell orders
            if q != 0:
                for k in target_prices:
                    try:
                        page.keyboard.press('S')
                        page.get_by_text("Regular").click()
                        page.get_by_role("spinbutton", name=security_sell_nse).click()
                        page.get_by_role("spinbutton", name=security_sell_nse).fill(q)
                        page.get_by_text("Limit").click()
                        time.sleep(2)
                        page.get_by_role("spinbutton", name="Price", exact=True).click()
                        page.get_by_role("spinbutton", name="Price", exact=True).press("ControlOrMeta+a")
                        page.get_by_role("spinbutton", name="Price", exact=True).fill(k)
                        time.sleep(2)
                        page.get_by_role("button", name="Sell").click()
                        time.sleep(2)
                    except Exception as e:
                        page.keyboard.press('S')
                        page.get_by_text("Regular").click()
                        page.get_by_role("spinbutton", name=security_sell_bse).click()
                        page.get_by_role("spinbutton", name=security_sell_bse).fill(q)
                        page.get_by_text("Limit").click()
                        time.sleep(2)
                        page.get_by_role("spinbutton", name="Price", exact=True).click()
                        page.get_by_role("spinbutton", name="Price", exact=True).press("ControlOrMeta+a")
                        page.get_by_role("spinbutton", name="Price", exact=True).fill(k)
                        time.sleep(2)
                        page.get_by_role("button", name="Sell").click()
                        time.sleep(2)

            logger.audit(f"AUDIT: Sell order placed | User: {user_id} | Symbol: {security_symbol} | Qty: {q} x {len(target_prices)} | Prices: {target_prices}")
            legacy_logger(file_path, amt_symbl, "Sold")
            return True, f"Sell orders initiated successfully"

        except Exception as e:
            logger.exception(f"Sell orders failed for {security_symbol} (User: {user_id}): {e}")
            legacy_logger(file_path, amt_symbl, "not Sold for some Exception")
            return False, f"Sell orders failed: {str(e)}"

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)