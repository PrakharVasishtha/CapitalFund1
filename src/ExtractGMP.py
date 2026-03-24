import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz


def normalize(name):
    return (
        name.lower()
        .replace("ipo", "")
        .replace("limited", "")
        .replace("ltd", "")
        .strip()
    )


def get_ipo_gmp(company_name="Notavalaible", min_match=65):
    url = "https://www.ipowatch.in/ipo-grey-market-premium-latest/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except:
        try:
            r = requests.get(url, headers=headers, timeout=12)
            r.raise_for_status()
        except Exception as e :
            print("Exception:",e)

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")

    if not table:
        raise Exception("GMP table not found — website layout changed")

    rows = table.find_all("tr")[1:]

    target = normalize(company_name)
    best_match = None
    best_score = 0

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 5:
            continue

        ipo_name = cols[0]
        #print(ipo_name)
        try:
            score = fuzz.partial_ratio(target, normalize(ipo_name))
        except:
            score = 50

        if score > best_score:
            best_score = score
            best_match = (ipo_name, cols)
    #print("Name Match for GMP:", best_score)
    gmp=.235
    if best_score >= min_match:
        gmp=best_match[1][3].replace("%", "").strip()
    #print("GMP:", gmp)
    if gmp == .235:
        return gmp
    elif gmp == "-":
        gmp = 0
        return gmp
    else:
        gmp = float(gmp)
        return gmp


# ----------- USAGE ------------
name = "Notavalaible"
#result = get_ipo_gmp(name)
#print(result)
