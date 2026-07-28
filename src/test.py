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


def get_gmp_percent(company_name: str, url: str = "https://www.ipopremium.in/", cutoff: float = 80.0) -> str:
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    try:
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching website: {e}"

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr")
    print(rows)
    search_term = normalize_text(company_name)

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        raw_name = cols[0].get_text()
        cleaned_name = normalize_text(raw_name)[:21]

        # Calculate similarity score (returns a float between 0.0 and 100.0)
        similarity_score = fuzz.token_sort_ratio(search_term, cleaned_name)
        print(similarity_score)
        # Check if similarity meets the 80% cutoff threshold
        if similarity_score >= cutoff:
            raw_gmp = cols[2].get_text(strip=True)
            raw_price_band = cols[5].get_text(strip=True)

            try:
                gmp_val = float(re.findall(r"\d+(?:\.\d+)?", raw_gmp)[0])
                prices = re.findall(r"\d+(?:\.\d+)?", raw_price_band)

                if prices:
                    upper_price = float(prices[-1])
                    if upper_price > 0:
                        pct = (gmp_val / upper_price) * 100
                        pct = round(pct, 2)
                        return pct
            except (IndexError, ValueError, ZeroDivisionError):
                return "0.0"

    return "0.0"


if __name__ == "__main__":
    # Will match even with minor typos or extra legal suffixes (e.g., "Manipal Health Ltd")
    print(get_gmp_percent("Manipal Health Enterp"))