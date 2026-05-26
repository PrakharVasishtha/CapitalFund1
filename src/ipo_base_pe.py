import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

def parse_float(val: Any) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return 0.0
    val = val.replace('%', '').replace('x', '').replace(',', '').replace('₹', '').replace('Cr', '').strip()
    try:
        x=float(val)
        if x <0:
            x = 0.0
        return x   
    except ValueError:
        return 0.0


def get_pe(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    prepe = 0
    pope = 0
    for row in soup.find_all("tr"):
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if "P/E" in "".join(cells[:2]):
            prepe = cells[1]
            pope = cells[2]
            #print(f"Pre-IPO  P/E : {prepe}")
            #print(f"Post-IPO P/E : {pope}")
            break
        else :
            prepe = 0
            pope = 0
    prepe = parse_float(prepe)
    pope = parse_float(pope)
    return prepe, pope


def get_peers_pe(url):
    HEADERS = {
        "User-Agent": "Mozilla/5.0"
    }
    recommended_url = url.replace("/ipo/", "/ipo-recommendation/", 1)
    response = requests.get(recommended_url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception("Failed to fetch page")

    soup = BeautifulSoup(response.text, "html.parser")

    peers_data = []
    peers_pe = []
    # Find all tables and look for relevant ones
    tables = soup.find_all("table")

    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]

        # Check if this table looks like a peers table
        if any("pe" in h or "p/e" in h for h in headers):
            rows = table.find_all("tr")[1:]  # skip header row

            for row in rows:
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cols) >= 2:
                    peers_data.append(cols)

            for row in peers_data:
                x=row[4]
                x = parse_float(x)
                if x > 0:
                    peers_pe.append(x)
                #print(x)
    #print(peers_pe)
    if not peers_data:
        print("No peers P/E data found.")
    return peers_pe


#url = "https://www.chittorgarh.com/ipo/fractal-industries-ipo/2780/"
#url = "https://www.chittorgarh.com/ipo/shayona-engineering-ipo/2173/"
#url = "https://www.chittorgarh.com/ipo/apsis-aerocom-ipo/2752/"
#print(get_pe(url))
#print(get_peers_pe(url))
#print(len(get_peers_pe(url)))
