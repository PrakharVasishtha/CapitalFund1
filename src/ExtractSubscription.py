from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from bs4 import BeautifulSoup

def get_ipo_subscription_live(url: str):
    url = url.replace("/ipo/", "/ipo_subscription/")  # better to use dedicated page

    options = Options()
    options.add_argument("--headless")  # run without UI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    driver = webdriver.Chrome(options=options)  # assumes chromedriver in PATH
    driver.get(url)

    try:
        # Wait up to 20 seconds for the subscription table to be present and have rows
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tr td"))
        )
        # Extra safety: wait a bit more if needed
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Now find the table (same logic as before, but now it has content)
        tables = soup.find_all("table")
        subscription_table = None
        for table in tables:
            if table.find(string=lambda x: x and "Subscription" in x):
                subscription_table = table
                break

        if not subscription_table:
            raise Exception("Subscription table still not found after wait")

        # Extract rows (adapt your parsing logic here)
        rows = subscription_table.find_all("tr")
        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]

        data = {}
        for row in rows[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 2:
                continue
            cat = cols[0].lower().replace("*", "").strip()
            sub_str = cols[1].replace("×", "").replace("times", "").strip() if len(cols) > 1 else ""
            try:
                val = float(sub_str) if sub_str else 0.0
            except:
                val = 0.0

            if "qib" in cat:
                data["QIB"] = val
            elif "nii" in cat and "aggregate" not in cat.lower() and "total" not in cat:
                if "NII" not in data:  # take main/aggregate NII
                    data["NII"] = val
            elif "individual" in cat or "retail" in cat or "rii" in cat:
                data["Retail"] = val
            elif "total" in cat and "anchor" not in cat:
                data["Total"] = val
        #print(data)
        nii = "h"
        qi = "h"
        rt = "h"
        ts = "h"
        
        if len(data) != 0:
            qi = str(data.get("QIB", 0.0))
            nii = str(data.get("NII", 0.0))
            rt = str(data.get("Retail", 0.0))
            ts = str(data.get("Total", 0.0))

        else:
            qi = "20"
            nii = "20"
            rt = "10"
            ts = "20"
        if len(qi) == 0:
            qi = nii
        qi = float(qi)
        nii = float(nii)
        rt = float(rt)
        ts = float(ts)
        sub= [qi,nii,rt,ts]
        return sub

    finally:
        driver.quit()


def get_ipo_subscription_dict(url: str):
    url=url.replace("/ipo/", "/ipo_subscription/")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")

    subscription_table = None
    for table in tables:
        if table.find(string=lambda x: x and "Subscription" in x):
            subscription_table = table
            break

    if subscription_table is None:
        raise Exception("Subscription table not found")

    rows = subscription_table.find_all("tr")
    headers_row = [th.get_text(strip=True) for th in rows[0].find_all("th")]

    data = []
    for row in rows[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) == len(headers_row):
            data.append(dict(zip(headers_row, cols)))
    result=data

    nii = "h"
    qi = "h"
    rt = "h"
    ts = "h"
    if len(result) != 0:
        nii = str(result[1].get('Subscription (times)', "0"))
        qi = str(result[0].get('Subscription (times)', "0"))
        rt = str(result[2].get('Subscription (times)', "0"))
        ts = str(result[3].get('Subscription (times)', "0"))

    else:
        qi = "2"
        nii = "5"
        rt = "1"
        ts = "2"

    if len(qi) == 0:
        qi = nii
    qi = float(qi)
    nii = float(nii)
    rt = float(rt)
    ts = float(ts)
    sub= [qi,nii,rt,ts]

    return sub
# Usage
#url = "https://www.chittorgarh.com/ipo/digilogic-systems-ipo/2617/"
#print(get_ipo_subscription_dict(url))