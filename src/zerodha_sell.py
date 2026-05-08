# zerodha_withdraw.py
import re
import time
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional

def zerodha_sell(
        user_id: str,
        password: str,
        totp_secret: str,
        security_symbol: str,
        headless: bool = False,
        timeout: int = 5000,
) -> tuple[bool, str]:
    def run(playwright: Playwright) -> tuple[bool, str]:
        print("______zerodha_sell___",user_id,":",security_symbol)
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
                p1 = str(round(Base.parse_float(p * 1.0025),2))
                p2 = str(round(Base.parse_float(p * 1.005),2))
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
                print("Holdings Inside:",holdings)
                page.get_by_role("button", name="Cancel").click()
            except Exception as e:
                holdings = 0
                print(e)
                
            print("holdings:",holdings)
            if holdings!=0: q = str(int(int(holdings) / 2))
            else: q = 0

            print("holdings:",holdings,"q:",q,"p:",p,"target_prices:",target_prices)
            
            
            # Buy 5 orders
            if q!=0:
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
                        print(e)
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

            return True, f"Sell orders initiated successfully"

        except Exception as e:
            import traceback
            return False, f"Sell orders failed: {str(e)}\n{traceback.format_exc()}"

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)