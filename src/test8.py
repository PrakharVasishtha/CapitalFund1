import requests
from bs4 import BeautifulSoup

url = "https://www.chittorgarh.com/ipo/central-mine-planning-design-institute-ipo/2456/"
soup = BeautifulSoup(requests.get(url).text, "html.parser")

for row in soup.find_all("tr"):
    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
    if "P/E" in "".join(cells[:2]):
        prepe = cells[1]
        pope = cells[2]
        print(f"Pre-IPO  P/E : {prepe}")
        print(f"Post-IPO P/E : {pope}")
        break