import sys
import os
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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
print("Headers:", header_cols)

target = "molbio"
for tr in rows[1:]:
    cols = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
    if cols and target in cols[0].lower():
        print("Found Molbio Row:")
        print("Raw cols:", cols)
        # Check indices
        name = cols[0]
        tot = cols[1]
        qib = cols[2]
        shni = cols[3]
        bhni = cols[4]
        nii = cols[5]
        rii = cols[6]
        print(f"Total: {tot}, QIB: {qib}, sHNI: {shni}, bHNI: {bhni}, NII: {nii}, Retail: {rii}")
