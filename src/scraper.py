import requests
import time
from bs4 import BeautifulSoup
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from base_ipo import categorize_ipo_industry, get_industry_score
import platform


def get_latest_ipos():
    """
    Scrapes the latest IPO listings from Chittorgarh (all IPOs - Mainboard + SME).
    Now correctly uses the 'Issue Type' column for reliable categorization.
    """
    url = "https://www.chittorgarh.com/report/ipo-in-india-list-main-board-sme/82/"

    try:
        options = Options()
        #options.add_argument("--headless")   # Uncomment when stable
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

        if platform.system() == "Windows":
            driver = webdriver.Chrome(options=options)
        else:
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        time.sleep(6)  # Increased slightly for safety
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        ipos = []
        table = soup.find('table')
        if not table:
            print("No table found on the page.")
            return []

        rows = table.find_all('tr')[1:]  # Skip header row

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 8:
                continue

            # Column 0: Company Name + Link
            name_cell = cells[0]
            name = name_cell.text.strip()
            ipo_url = None
            link = name_cell.find('a')
            if link and link.get('href'):
                ipo_url = link['href'] if link['href'].startswith('http') else 'https://www.chittorgarh.com' + link[
                    'href']

            # === NEW: Use 'Issue Type' column (usually cells[1]) ===
            issue_type_cell = cells[1]
            issue_type = issue_type_cell.text.strip().upper()

            if "SME" in issue_type:
                category = "SME"
            else:
                category = "Mainboard"

            # Fallback: If Issue Type is empty/missing, check Listing at column
            if not issue_type or issue_type in ["", "—", "-"]:
                listing_at = cells[6].text.strip() if len(cells) > 6 else ""
                if "SME" in listing_at.upper():
                    category = "SME"
                else:
                    category = "Mainboard"

            # Opening date for year extraction
            open_date = cells[2].text.strip() if len(cells) > 2 else ""  # Adjusted index if needed
            year = open_date.split(',')[-1].strip() if ',' in open_date else str(datetime.datetime.now().year)
            industry = categorize_ipo_industry(name)
            industry_score = get_industry_score(industry)
            ipos.append({
                'name': name,
                'category': category,
                'year': year,
                'url': ipo_url,
                'issue_type_raw': issue_type,
                'industry_score': industry_score,
            })

        print(f"Fetched {len(ipos)} IPOs from Chittorgarh. "
              f"Mainboard: {sum(1 for i in ipos if i['category'] == 'Mainboard')}, "
              f"SME: {sum(1 for i in ipos if i['category'] == 'SME')}")

        return ipos

    except Exception as e:
        print(f"Error scraping IPO list: {e}")
        return []
