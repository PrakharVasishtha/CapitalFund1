import re
import unicodedata
from bs4 import BeautifulSoup
import cloudscraper
from rapidfuzz import fuzz


def normalize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = unicodedata.normalize("NFKD", text).replace("\xa0", " ")
    return " ".join(cleaned.split()).lower()


def clean_name_for_gmp(text: str) -> str:
    if not text:
        return ""
    s = str(text).replace('&amp;', '&').strip()
    s = re.sub(r'\s*(?:Price|GMP|Date|Pric|Pr|GM|Review|Details|Ltd|Limited|NSE|BSE|SME|Mainboard)\b.*$', '', s, flags=re.IGNORECASE).strip()
    return normalize_text(s)


def get_ipo_gmp(company_name: str, url: str = "https://www.ipopremium.in/", cutoff: float = 70.0) -> float:
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    try:
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching GMP website: {e}")
        return 0.0

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")
    search_clean = clean_name_for_gmp(company_name)
    if not search_clean:
        return 0.0

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue
        raw_name = cols[0].get_text()
        row_clean = clean_name_for_gmp(raw_name)
        if not row_clean:
            continue

        score1 = fuzz.token_sort_ratio(search_clean, row_clean)
        score2 = fuzz.partial_ratio(search_clean, row_clean)
        best_score = max(score1, score2)

        match = (best_score >= cutoff) or (search_clean in row_clean) or (row_clean in search_clean)
        if match:
            raw_gmp = cols[2].get_text(strip=True)
            raw_price_band = cols[5].get_text(strip=True)

            try:
                gmp_match = re.findall(r"\d+(?:\.\d+)?", raw_gmp)
                if not gmp_match:
                    return 0.0
                gmp_val = float(gmp_match[0])
                prices = re.findall(r"\d+(?:\.\d+)?", raw_price_band)

                if prices:
                    upper_price = float(prices[-1])
                    if upper_price > 0:
                        pct = round((gmp_val / upper_price) * 100, 2)
                        return pct
            except (IndexError, ValueError, ZeroDivisionError):
                return 0.0

    return 0.0
#print(get_ipo_gmp("MV Electrosystems Ltd"))