import sys
import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.investorgain.com/report/ipo-subscription-live/333/"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=25000)
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, "html.parser")
table = soup.find("table")
rows = table.find_all("tr")

header_cols = [c.get_text(strip=True).lower() for c in rows[0].find_all(["td", "th"])]
print("Header cols raw:", header_cols)
col_map = {}
for idx, h_raw in enumerate(header_cols):
    h = re.sub(r'[^a-z0-9]', '', h_raw)
    if "name" in h or "company" in h: col_map["name"] = idx
    elif h == "total" or "total" in h: col_map["total"] = idx
    elif h == "qib" or "qib" in h: col_map["qib"] = idx
    elif h == "nii": col_map["nii"] = idx
    elif h == "rii" or "retail" in h: col_map["rii"] = idx

if "nii" not in col_map:
    for idx, h_raw in enumerate(header_cols):
        h = re.sub(r'[^a-z0-9]', '', h_raw)
        if h == "nii" or (("nii" in h or "noninstitutional" in h) and "shni" not in h and "bhni" not in h):
            col_map["nii"] = idx
            break

print("col_map:", col_map)

key_clean = "molbio"
for tr in rows[1:]:
    cols = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
    if len(cols) <= col_map["name"]:
        continue
    r_name = re.sub(r'[^a-z0-9]', '', cols[col_map["name"]].lower())
    print("Checking row:", r_name)
    if key_clean and (key_clean in r_name or r_name in key_clean or key_clean[:4] in r_name):
        print("MATCHED!")
        qib_str = cols[col_map["qib"]] if "qib" in col_map and col_map["qib"] < len(cols) else ""
        nii_str = cols[col_map["nii"]] if "nii" in col_map and col_map["nii"] < len(cols) else ""
        rii_str = cols[col_map["rii"]] if "rii" in col_map and col_map["rii"] < len(cols) else ""
        total_str = cols[col_map["total"]] if "total" in col_map and col_map["total"] < len(cols) else ""
        print(f"Strings: QIB='{qib_str}', NII='{nii_str}', RII='{rii_str}', Total='{total_str}'")
