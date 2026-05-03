# zerodha_withdraw.py
import re
import time
import Base
from playwright.sync_api import Playwright, sync_playwright, expect, Page
import pyotp
from typing import Optional

def get_margin(page):
    selectors = [
        # primary (clean)
        lambda: page.locator("div:has-text('Available margin') .value").first.inner_text(),

        # fallback 1 (relative)
        lambda: page.get_by_text("Available margin").locator("..").locator(".value").inner_text(),

        # fallback 2 (loose match)
        lambda: page.locator(":text('Available margin')").locator("xpath=..").locator(".value").inner_text(),

        # fallback 3 (generic grab near funds page)
        lambda: page.locator(".value").nth(0).inner_text(),
    ]

    for fn in selectors:
        try:
            val = fn()
            if val and any(char.isdigit() for char in val):
                return val
        except:
            continue

    raise Exception("Margin not found")

def parse_money(text):
    return float(re.sub(r"[^\d.]", "", text))

def get_balance_zerodha(
        user_id: str,
        password: str,
        totp_secret: str,
        headless: bool = False,
        timeout: int = 5000,
) -> int:

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
            # Wait for dashboard to load
            page.wait_for_selector("text=Funds")
            page.get_by_role("link", name="Funds").click()
            page.wait_for_selector("text=Available margin")

            margin_text = get_margin(page)
            margin_value = parse_money(margin_text)

            print("Margin:", margin_value)



            return margin_value

        except Exception as e:
            import traceback
            return 1

        finally:
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()

    # ── Execute ─────────────────────────────────────────────────────
    with sync_playwright() as playwright:
        return run(playwright)
