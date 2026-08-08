"""
special_session_indicative_price_bse.py
========================================
Fetches listing day pre-open / indicative price for BSE listed IPO stocks.
Supports both fast BSE API lookup (if scripcode provided) and Playwright
web scraping on the BSE India website.
"""
import re
import time
import requests
from playwright.sync_api import Playwright, sync_playwright


def get_bse_price_api(scripcode: str) -> float:
    """Fast BSE API call for a numeric scripcode."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Referer": "https://www.bseindia.com/",
        }
        url = f"https://api.bseindia.com/BseIndiaAPI/api/GetScripHeaderData/w?DebtFlag=&scripcode={scripcode}&seriesid="
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            header = data.get("Header", {})
            curr_rate = data.get("CurrRate", {})

            # Priority 1: Special session / pre-open indicative price
            pre_open_price = header.get("PRE_OPEN_I_PRICE") or header.get("PCAS_INDICATIVE_PRICE")
            if pre_open_price:
                cleaned = re.sub(r"[^\d.]", "", str(pre_open_price))
                if cleaned:
                    return float(cleaned)

            # Priority 2: Open price / LTP
            ltp = curr_rate.get("LTP") or header.get("LTP") or header.get("Open")
            if ltp:
                cleaned = re.sub(r"[^\d.]", "", str(ltp))
                if cleaned:
                    return float(cleaned)
    except Exception as e:
        print(f"BSE API error for scripcode {scripcode}: {e}")
    return 0.0


def ipo_indicative_price_bse(
        ipo_name: str,
        exchange: str = "BSE",
        headless: bool = True,
        timeout: int = 15000,
) -> float:
    """
    Fetches pre-open / indicative listing price for an IPO on BSE exchange.
    If ipo_name is numeric (scripcode), uses fast BSE API lookup.
    Otherwise uses Playwright to search BSE India website and extract rate from #idcrval.
    """
    ipo_name_clean = str(ipo_name).strip() if ipo_name else ""
    if not ipo_name_clean:
        return 0.0

    # If scripcode is passed directly (digits only)
    if ipo_name_clean.isdigit():
        price = get_bse_price_api(ipo_name_clean)
        if price > 0:
            return price

    def run(playwright: Playwright) -> float:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        page.set_default_timeout(timeout)
        price_val = 0.0

        try:
            page.goto("https://www.bseindia.com/", wait_until="domcontentloaded")
            time.sleep(1)

            try:
                page.get_by_role("button", name="Close").click(timeout=2000)
            except Exception:
                pass

            search_box = page.get_by_role("textbox", name="smart search")
            search_box.click()
            search_box.fill(ipo_name_clean)
            time.sleep(1.5)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            time.sleep(2)

            raw_text = page.locator("#idcrval").inner_text(timeout=5000)
            print(f"BSE rate text for {ipo_name_clean}: {raw_text}")
            cleaned = re.sub(r"[^\d.]", "", raw_text)
            if cleaned:
                price_val = float(cleaned)
        except Exception as e:
            print(f"ipo_indicative_price_bse Error for {ipo_name_clean}: {e}")
        finally:
            context.close()
            browser.close()

        return price_val

    with sync_playwright() as playwright:
        return run(playwright)


# Alias for convenience
get_ipo_indicative_price_bse = ipo_indicative_price_bse

if __name__ == "__main__":
    p = ipo_indicative_price_bse("544026", "BSE")
    print(f"Fetched BSE price for IREDA (544026): {p}")
