import requests
import time
from bs4 import BeautifulSoup
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from ipo_base import categorize_ipo_industry, get_industry_score
import platform
from logger_setup import get_logger

logger = get_logger(__name__)

# P2-4: Maximum Selenium retries and backoff constant
_MAX_SCRAPE_RETRIES = 3
_SCRAPE_BACKOFF_BASE = 8   # seconds; doubles each retry


def _parse_ipo_table(soup: "BeautifulSoup") -> list:
    """Extract IPO rows from a BeautifulSoup-parsed Chittorgarh page."""
    ipos = []
    table = soup.find("table")
    if not table:
        logger.warning("No table found on the page.")
        return []

    rows = table.find_all("tr")[1:]  # Skip header row
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 8:
            continue

        # Column 0: Company Name + Link
        name_cell = cells[0]
        name = name_cell.text.strip()
        ipo_url = None
        link = name_cell.find("a")
        if link and link.get("href"):
            ipo_url = link["href"] if link["href"].startswith("http") else "https://www.chittorgarh.com" + link["href"]

        # Column 1: Issue Type — reliable SME vs Mainboard indicator
        issue_type = cells[1].text.strip().upper()
        if "SME" in issue_type:
            category = "SME"
        else:
            category = "Mainboard"

        # Fallback via Listing-at column
        if not issue_type or issue_type in ("", "—", "-"):
            listing_at = cells[6].text.strip() if len(cells) > 6 else ""
            category = "SME" if "SME" in listing_at.upper() else "Mainboard"

        open_date = cells[2].text.strip() if len(cells) > 2 else ""
        year = open_date.split(",")[-1].strip() if "," in open_date else str(datetime.datetime.now().year)
        industry = categorize_ipo_industry(name)
        industry_score = get_industry_score(industry)
        ipos.append({
            "name": name,
            "category": category,
            "year": year,
            "url": ipo_url,
            "issue_type_raw": issue_type,
            "industry_score": industry_score,
        })
    return ipos


def get_latest_ipos() -> list:
    """
    Scrapes the latest IPO listings from Chittorgarh (all IPOs — Mainboard + SME).

    P2-4: Retries up to 3 times with exponential back-off if Selenium encounters
    a transient network error.  Falls back to a plain requests GET if all
    Selenium attempts fail.
    """
    url = "https://www.chittorgarh.com/report/ipo-in-india-list-main-board-sme/82/"

    options = Options()
    # options.add_argument("--headless")  # Uncomment when stable
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_SCRAPE_RETRIES + 1):
        driver = None
        try:
            if platform.system() == "Windows":
                driver = webdriver.Chrome(options=options)
            else:
                service = Service("/usr/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=options)

            driver.get(url)
            time.sleep(6)   # Allow JS to render
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
            driver = None

            ipos = _parse_ipo_table(soup)
            logger.info(
                f"Fetched {len(ipos)} IPOs from Chittorgarh (attempt {attempt}). "
                f"Mainboard: {sum(1 for i in ipos if i['category'] == 'Mainboard')}, "
                f"SME: {sum(1 for i in ipos if i['category'] == 'SME')}"
            )
            return ipos

        except Exception as exc:
            last_exc = exc
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            backoff = _SCRAPE_BACKOFF_BASE * (2 ** (attempt - 1))
            logger.warning(
                f"Selenium scrape attempt {attempt}/{_MAX_SCRAPE_RETRIES} failed: {exc}. "
                f"Retrying in {backoff}s…"
            )
            if attempt < _MAX_SCRAPE_RETRIES:
                time.sleep(backoff)

    # ── Requests fallback ─────────────────────────────────────────────────────
    logger.warning(
        f"All {_MAX_SCRAPE_RETRIES} Selenium attempts failed ({last_exc}). "
        "Trying plain requests fallback…"
    )
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        ipos = _parse_ipo_table(soup)
        logger.info(f"Requests fallback fetched {len(ipos)} IPOs.")
        return ipos
    except Exception as fb_exc:
        logger.error(f"Requests fallback also failed: {fb_exc}", exc_info=True)
        return []
