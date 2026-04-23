# zerodha_withdraw.py
import re
import time
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional


def zerodha_buy(
        user_id: str,
        password: str,
        totp_secret: str,
        amount: int,
        security_symbol: str,
        headless: bool = False,
        timeout: int = 45000,
) -> tuple[bool, str]:

    amount_str = str(int(float(amount)))  # Zerodha usually wants whole numbers

    def run(playwright: Playwright) -> tuple[bool, str]:
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
            page.mouse.click(100, 200);
            time.sleep(.5)

            # Price amount determination
            page.keyboard.press('PageDown')
            time.sleep(1)
            page.keyboard.press('B')
            page.get_by_text("Regular").click()
            page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").click()
            page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").fill("1")
            page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").press("Tab")
            price = page.get_by_role("spinbutton", name="Price", exact=True).input_value()
            page.get_by_role("button", name="Cancel").click()
            print(type(price))
            p = Base.parse_float(price)
            q = int((amount/5 - 1) / p)
            p1 = Base.parse_float(p * .995)
            p2 = Base.parse_float(p * .990)
            p3 = Base.parse_float(p * .985)
            p4 = Base.parse_float(p * .980)
            p5 = Base.parse_float(p * .975)
            print(p, p1, p2, p3, p4, p5)
            target_prices = [p1, p2, p3, p4, p5]

            # Buy 5 orders
            for k in target_prices:
                page.keyboard.press('B')
                page.get_by_text("Regular").click()
                page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").click()
                page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").fill(q)
                page.get_by_role("spinbutton", name="BUY NIFTYIETF (NSE) quantity").press("Tab")
                page.get_by_role("spinbutton", name="Price", exact=True).fill(k)
                page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
                page.get_by_role("button", name="Buy").click()
                time.sleep(2)

            return True, f"buy orders initiated successfully"

        except Exception as e:
            import traceback
            return False, f"buy orders failed: {str(e)}\n{traceback.format_exc()}"

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

def zerodha_sell(
        user_id: str,
        password: str,
        totp_secret: str,
        security_symbol: str,
        headless: bool = False,
        timeout: int = 45000,
) -> tuple[bool, str]:

    def run(playwright: Playwright) -> tuple[bool, str]:
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
            page.mouse.click(100, 200);
            time.sleep(.5)

            # Price quantity determination
            page.keyboard.press('PageDown')
            time.sleep(1)
            page.keyboard.press('S')
            page.get_by_text("Regular").click()
            page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").click()
            page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").fill("1")
            page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").press("Tab")
            price = page.get_by_role("spinbutton", name="Price", exact=True).input_value()
            holdings = page.get_by_role("spinbutton", name="holdings", exact=True).input_value() 
            page.get_by_role("button", name="Cancel").click()
            print(type(price))
            p = Base.parse_float(price)
            q = int(holdings/2)
            p1 = Base.parse_float(p * 1.005)
            p2 = Base.parse_float(p * 1.01)
            print(p, p1, p2)
            target_prices = [p1, p2]

            # Buy 5 orders
            for k in target_prices:
                page.keyboard.press('S')
                page.get_by_text("Regular").click()
                page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").click()
                page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").fill(q)
                page.get_by_role("spinbutton", name="SELL NIFTYIETF (NSE) quantity").press("Tab")
                page.get_by_role("spinbutton", name="Price", exact=True).fill(k)
                page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
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
