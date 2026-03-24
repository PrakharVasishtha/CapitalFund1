import requests
import time
from bs4 import BeautifulSoup
import datetime  # For fallback year if parsing fails
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_latest_ipos():
    """
    Scrapes the latest IPO listings from Chittorgarh (all IPOs, including Mainboard and SME),
    categorizes them based on 'Listing at', and includes the detail page URL for each IPO.
    Returns a list of dicts with basic IPO details (no financial data).
    """
    url = "https://www.chittorgarh.com/report/ipo-in-india-list-main-board-sme/82/"  # Comprehensive list for current year
    try:
        # Set up Selenium for browser simulation to avoid blocking
        options = Options()
        #options.add_argument("--headless")  # Run headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        ipos = []
        table = soup.find('table')  # No class; assuming this is the main IPO table
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:  # Ensure enough columns (headers have 9)
                    name_cell = cells[0]
                    name = name_cell.text.strip()
                    ipo_url = None
                    link = name_cell.find('a')
                    if link and link.get('href'):
                        ipo_url = link['href'] if link['href'].startswith('http') else 'https://www.chittorgarh.com' + link['href']
                    listing_at = cells[6].text.strip()
                    category = 'SME' if 'SME' in listing_at else 'Mainboard'
                    # Parse year from opening date (e.g., "Tue, Jan 13, 2026" -> "2026")
                    open_date = cells[1].text.strip()
                    year = open_date.split(',')[-1].strip() if ',' in open_date else str(datetime.datetime.now().year)
                    ipos.append({
                        'name': name,
                        'category': category,
                        'year': year,
                        'url': ipo_url
                        # Add more basic fields if needed, e.g., 'open_date': open_date
                    })
        print(f"Fetched {len(ipos)} IPOs from Chittorgarh.")
        return ipos
    except Exception as e:
        print(f"Error scraping IPO list: {e}")
        return []

#get_latest_ipos()