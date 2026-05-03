import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def clean_number(text):
    text = text.lower()
    text = text.replace("×", "").replace("x", "").replace("times", "").strip()
    num = re.sub(r"[^\d.]", "", text)
    return float(num) if num else 0.0

def get_ipo_subscription_live(url: str):
    url = url.replace("/ipo/", "/ipo_subscription/")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find correct table
        tables = soup.find_all("table")
        subscription_table = None
        for table in tables:
            if "Subscription" in table.get_text():
                subscription_table = table
                break

        if not subscription_table:
            return None

        rows = subscription_table.find_all("tr")

        # ✅ Detect correct column index
        header_cols = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]

        sub_idx = None
        for i, h in enumerate(header_cols):
            if "subscription" in h:
                sub_idx = i
                break

        if sub_idx is None:
            raise Exception("Subscription column not found")

        data = {
            "QIB": 0.0,
            "NII": 0.0,
            "Retail": 0.0,
            "Total": 0.0
        }

        # ✅ Parse rows
        for row in rows[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]

            if len(cols) <= sub_idx:
                continue

            category = cols[0].lower()
            val = clean_number(cols[sub_idx])  # ✅ correct

            # QIB
            if any(k in category for k in ["qib", "qualified institutional"]):
                data["QIB"] = val

            # NII / HNI
            elif any(k in category for k in ["nii", "hni", "non institutional"]):
                data["NII"] = val

            # Retail
            elif any(k in category for k in ["retail", "rii", "individual"]):
                data["Retail"] = val

            # Total
            elif "total" in category and "anchor" not in category:
                data["Total"] = val

        return [
            data["QIB"],
            data["NII"],
            data["Retail"],
            data["Total"]
        ]

    finally:
        driver.quit()


def get_ipo_subscription_dict(url: str):
    url = url.replace("/ipo/", "/ipo_subscription/")

    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find correct table
    tables = soup.find_all("table")
    subscription_table = None
    for table in tables:
        if "Subscription" in table.get_text():
            subscription_table = table
            break

    if not subscription_table:
        return None

    rows = subscription_table.find_all("tr")

    # ✅ Detect column index dynamically
    header_cols = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]

    sub_idx = None
    for i, h in enumerate(header_cols):
        if "subscription" in h:
            sub_idx = i
            break

    if sub_idx is None:
        raise Exception("Subscription column not found")

    data = {
        "QIB": 0.0,
        "NII": 0.0,
        "Retail": 0.0,
        "Total": 0.0
    }

    # ✅ Parse rows using correct column
    for row in rows[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]

        if len(cols) <= sub_idx:
            continue

        category = cols[0].lower()
        value = clean_number(cols[sub_idx])  # ✅ FIXED

        cat = category.lower()

        # QIB
        if any(k in cat for k in ["qib", "qualified institutional"]):
            data["QIB"] = value

        # NII / HNI
        elif any(k in cat for k in ["nii", "hni", "non institutional"]):
            data["NII"] = value

        # Retail
        elif any(k in cat for k in ["retail", "rii", "individual"]):
            data["Retail"] = value

        # Total (exclude anchor)
        elif "total" in cat and "anchor" not in cat:
            data["Total"] = value

    return [
        data["QIB"],
        data["NII"],
        data["Retail"],
        data["Total"]
    ]



# Usage
#url = "https://www.chittorgarh.com/ipo/sai-parenterals-ipo/2681/"
#print(get_ipo_subscription_dict(url))
#print(get_ipo_subscription_live(url))