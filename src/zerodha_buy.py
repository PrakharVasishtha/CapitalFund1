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
        timeout: int = 5000,
) -> tuple[bool, str]:

    amount_str = str(int(float(amount)))  # Zerodha usually wants whole numbers

    def run(playwright: Playwright) -> tuple[bool, str]:
        print("-----",user_id,amount,security_symbol,"-----")
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
            security_buy = "BUY " + security_symbol + " (NSE) quantity"
            security_buy_nse = "BUY " + security_symbol + " (NSE) quantity"
            security_buy_bse = "BUY " + security_symbol + " (BSE) quantity"
            time.sleep(1)

            try:
                page.keyboard.press('B')
                page.get_by_text("Regular").click()
                page.get_by_role("spinbutton", name=security_buy_nse).click()
                page.get_by_role("spinbutton", name=security_buy_nse).fill("1")
                page.get_by_role("spinbutton", name=security_buy_nse).press("Tab")
                price = page.get_by_role("spinbutton", name="Price", exact=True).input_value()
                page.get_by_role("button", name="Cancel").click()
                time.sleep(1)
            except Exception as e:
                print(e)
                page.keyboard.press('B')
                page.get_by_text("Regular").click()
                page.get_by_role("spinbutton", name=security_buy_bse).click()
                page.get_by_role("spinbutton", name=security_buy_bse).fill("1")
                page.get_by_role("spinbutton", name=security_buy_bse).press("Tab")
                price = page.get_by_role("spinbutton", name="Price", exact=True).input_value()
                page.get_by_role("button", name="Cancel").click()
                time.sleep(1)
                
            time.sleep(1)
            print(price)
            p = Base.parse_float(price)
            q = str(int((amount/5 - 1) / p))
            p1 = str(round(Base.parse_float(p * .9975),2))
            p2 = str(round(Base.parse_float(p * .995),2))
            p3 = str(round(Base.parse_float(p * .9925),2))
            p4 = str(round(Base.parse_float(p * .99),2))
            p5 = str(round(Base.parse_float(p * .9875),2))
            print(p, p1, p2, p3, p4, p5)
            target_prices = [p1, p2, p3, p4, p5]

            # Buy 5 orders
            for k in target_prices:
                try:
                    page.keyboard.press('B')
                    page.get_by_text("Regular").click()

                    page.get_by_role("spinbutton", name=security_buy_nse).click()
                    page.get_by_role("spinbutton", name=security_buy_nse).fill(q)
                    time.sleep(1)
                    page.get_by_role("spinbutton", name=security_buy_nse).press("Tab")
                    page.get_by_role("spinbutton", name="Price", exact=True).fill(k)
                    time.sleep(1)
                    page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
                    page.get_by_role("button", name="Buy").click()
                    time.sleep(1)
                except Exception as e:
                    print(e)
                    page.keyboard.press('B')
                    page.get_by_text("Regular").click()

                    page.get_by_role("spinbutton", name=security_buy_bse).click()
                    page.get_by_role("spinbutton", name=security_buy_bse).fill(q)
                    time.sleep(1)
                    page.get_by_role("spinbutton", name=security_buy_bse).press("Tab")
                    page.get_by_role("spinbutton", name="Price", exact=True).fill(k)
                    time.sleep(1)
                    page.get_by_role("spinbutton", name="Price", exact=True).press("Tab")
                    page.get_by_role("button", name="Buy").click()
                    time.sleep(1)

            return 1

        except Exception as e:
            import traceback
            return 0

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()
    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)