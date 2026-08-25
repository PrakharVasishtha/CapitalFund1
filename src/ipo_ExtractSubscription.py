import requests
from bs4 import BeautifulSoup
import re
import time
import platform
import logging

logger = logging.getLogger(__name__)

_IG_HTML_CACHE = None
_IG_CACHE_TIME = 0.0


def clean_number(text: str) -> float:
    if not text:
        return 0.0
    cleaned = re.sub(r'\d{1,2}(?:st|nd|rd|th)\s+[a-zA-Z]{3}.*$', '', text, flags=re.I).strip()
    cleaned = cleaned.lower().replace("x", "").replace("times", "").replace(",", "").strip()
    m = re.search(r'^(\d+(?:\.\d+)?)', cleaned)
    if m:
        try:
            val = float(m.group(1))
            if val <= 2500.0:
                return val
        except ValueError:
            pass
    return 0.0


def _get_investorgain_html() -> str:
    global _IG_HTML_CACHE, _IG_CACHE_TIME
    now = time.time()
    if _IG_HTML_CACHE and (now - _IG_CACHE_TIME < 300):
        return _IG_HTML_CACHE

    url = "https://www.investorgain.com/report/ipo-subscription-live/333/"
    html = ""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000, wait_until="networkidle")
            html = page.content()
            browser.close()
    except Exception as pw_exc:
        logger.warning("Playwright fetch error for InvestorGain: %s", pw_exc)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                html = resp.text
        except Exception:
            pass

    if html and len(html) > 50000:
        _IG_HTML_CACHE = html
        _IG_CACHE_TIME = now

    return html or ""


def fetch_investorgain_live(company_keyword: str = "") -> list:
    """
    Primary helper to fetch real-time live subscription figures [QIB, NII, Retail, Total] from InvestorGain desk.
    Uses 300s cached Playwright DOM html.
    """
    try:
        html = _get_investorgain_html()
        if not html:
            return [0.0, 0.0, 0.0, 0.0]

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return [0.0, 0.0, 0.0, 0.0]

        rows = table.find_all("tr")
        if not rows:
            return [0.0, 0.0, 0.0, 0.0]

        header_cols = [c.get_text(strip=True).lower() for c in rows[0].find_all(["td", "th"])]
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

        if "name" not in col_map or not company_keyword:
            return [0.0, 0.0, 0.0, 0.0]

        key_clean = re.sub(r'[^a-z0-9]', '', company_keyword.lower())

        for tr in rows[1:]:
            cols = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cols) <= col_map["name"]:
                continue
            r_name = re.sub(r'[^a-z0-9]', '', cols[col_map["name"]].lower())
            if key_clean and (key_clean in r_name or r_name in key_clean or key_clean[:4] in r_name):
                qib = clean_number(cols[col_map["qib"]]) if "qib" in col_map and col_map["qib"] < len(cols) else 0.0
                nii = clean_number(cols[col_map["nii"]]) if "nii" in col_map and col_map["nii"] < len(cols) else 0.0
                rii = clean_number(cols[col_map["rii"]]) if "rii" in col_map and col_map["rii"] < len(cols) else 0.0
                total = clean_number(cols[col_map["total"]]) if "total" in col_map and col_map["total"] < len(cols) else 0.0
                return [qib, nii, rii, total]
    except Exception as exc:
        logger.warning("Error fetching InvestorGain live sub: %s", exc)

    return [0.0, 0.0, 0.0, 0.0]


def get_ipo_subscription_live(url: str):
    """
    Fetches live subscription figures [QIB, NII, Retail, Total].
    Prioritizes InvestorGain real-time live desk, falling back to Chittorgarh.
    """
    company_key = url.split("/ipo/")[-1].split("/")[0].replace("-ipo", "") if "/ipo/" in url else ""
    
    # 1. Try InvestorGain Live Desk Primary Source
    ig_res = fetch_investorgain_live(company_key)
    if ig_res[3] > 0:
        return ig_res

    # 2. Chittorgarh Detail Sub-Page Fallback
    sub_url = url.replace("/ipo/", "/ipo_subscription/")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(sub_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")
            data = {"QIB": 0.0, "NII": 0.0, "Retail": 0.0, "Total": 0.0}
            matched = False

            for t in tables:
                rows = t.find_all("tr")
                if not rows: continue
                headers_list = [[c.get_text(strip=True).lower() for c in tr.find_all(["td", "th"])] for tr in rows[:2]]
                hdr_str = " ".join(" ".join(r) for r in headers_list)
                if any(bad in hdr_str for bad in ["shares offered", "amt (₹ cr.)", "size (%)", "bid date"]):
                    continue

                for tr in rows:
                    cols = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                    if len(cols) >= 2:
                        cat = cols[0].lower()
                        if any(bad in cat for bad in ["shares", "amount", "price", "applications", "allocation", "allotted", "size"]):
                            continue
                        val = clean_number(cols[1])
                        if "qualified" in cat or "qib" in cat: data["QIB"] = val; matched = True
                        elif "non institutional" in cat or "nii" in cat: data["NII"] = val; matched = True
                        elif "retail" in cat or "rii" in cat: data["Retail"] = val; matched = True
                        elif "total" in cat and "anchor" not in cat: data["Total"] = val; matched = True

            if matched and data["Total"] > 0:
                return [data["QIB"], data["NII"], data["Retail"], data["Total"]]
    except Exception as exc:
        logger.warning("Error fetching Chittorgarh live sub: %s", exc)

    return [0.0, 0.0, 0.0, 0.0]


def get_ipo_subscription_dict(url: str):
    """
    Fetches subscription figures [QIB, NII, Retail, Total].
    Prioritizes InvestorGain real-time live desk, falling back to Chittorgarh.
    """
    return get_ipo_subscription_live(url)