from curl_cffi import requests # Drop standard requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import re
import time


def normalize(name):
    return (
        name.lower()
        .replace("ipo", "")
        .replace("limited", "")
        .replace("ltd", "")
        .strip()
    )

def extract_percent_gmp(cols, max_valid=98.0):
    """
    Extract ONLY % GMP and validate range.
    Reject unrealistic values.
    """
    for col in cols:
        text = col.strip()

        # Case 1: (23.42%)
        match = re.search(r"\(([\d.]+)\s*%\)", text)
        if match:
            val = float(match.group(1))
            if 0 <= val <= max_valid:
                return val
            else:
                return None  # reject bad value

        # Case 2: 23.42%
        match = re.search(r"([\d.]+)\s*%", text)
        if match:
            val = float(match.group(1))
            if 0 <= val <= max_valid:
                return val
            else:
                print(f"Rejected suspicious GMP: {val}")
                return None  # reject bad value

    return None


def get_ipo_gmp(company_name: str, min_match=65):
    url = "https://www.ipowatch.in/ipo-grey-market-premium-latest/"
    time.sleep(.5)
    r = requests.get(url, impersonate="chrome120", timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tables = soup.find_all("table")
    if not tables:
        raise Exception("No tables found")

    target = normalize(company_name)
    best_match = None
    best_score = 0

    # 🔥 scan ALL tables (not just one)
    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) < 2:
                continue

            ipo_name = cols[0]
            score = fuzz.partial_ratio(target, normalize(ipo_name))

            if score > best_score:
                best_score = score
                best_match = cols

    if not best_match or best_score < min_match:
        return None

    gmp = extract_percent_gmp(best_match)

    if gmp is None:
        return 0  # NOT 0

    return gmp


# ----------- USAGE ------------
#name = "MV Electrosystems"
#result = get_ipo_gmp(name)
#print(result)
