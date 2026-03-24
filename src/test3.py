import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_peers_pe(url):
    response = requests.get(url, headers=HEADERS)
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
                peers_pe.append(x)
                print(x)
    print(peers_pe)
    if not peers_data:
        print("No peers P/E data found.")
    return peers_pe


url = "https://www.chittorgarh.com/ipo-recommendation/gujarat-kidney-and-super-speciality-ipo/2289/"
data = get_peers_pe(url)
print(f"Peers P/E : {data}")