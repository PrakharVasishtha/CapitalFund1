import requests
from bs4 import BeautifulSoup

def has_dicey_word(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    page_text = soup.get_text(separator=" ", strip=True).lower()

    if "skipping" in page_text:
        x=0
    else:
        x=1
    return x



# Example usage
#url = "https://www.chittorgarh.com/ipo/modern-diagnostic-ipo/2276/"
#url = "https://www.chittorgarh.com/ipo/victory-electric-vehicles-ipo/2315/"
#print(has_dicey_word(url))