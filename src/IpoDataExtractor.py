# chittorgarh_ipo_extractor.py
import re
import requests
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from io import StringIO


@dataclass
class IPOData:
    company_name: str = ""
    url: str = ""
    issue_price_per_share: str = "N/A"
    gmp: str = "Not Available"
    ipo_timeline: Dict[str, str] = None
    ipo_details: Dict[str, str] = None
    lot_size: Dict[str, Any] = None
    financials: Dict[str, Any] = None
    ratios: Dict[str, Any] = None
    unit: str = "Crores"
    extracted_at: str = ""
    anchor_allocation: str = "No"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if
                v not in (None, {}, [], "N/A", "Not Available") or k in ["gmp", "issue_price_per_share", "unit"]}


class ChittorgarhIPOExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    @staticmethod
    def _clean_number(value) -> Optional[float]:
        if pd.isna(value) or value is None:
            return None
        s = re.sub(r'[₹,\sCrCRcr%]', '', str(value).strip(), flags=re.I)
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def _extract_amount(text: str) -> str:
        """Extract the first numeric amount like 69.68 from '₹69.68 crores' or '81.01 Cr'."""
        if not text:
            return ""
        # Find first number (with optional decimal point)
        num_match = re.search(r'[\d,]+\.?\d*', text)
        if num_match:
            # Remove commas
            num = re.sub(r',', '', num_match.group(0))
            return num
        return ""

    @staticmethod
    def _clean_amount_text(text: str) -> str:
        if not text:
            return ""
        return re.sub(r'[₹,\sCrCRcr]', '', text.strip(), flags=re.I)

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip() if text else ""

    def _fetch(self, url: str) -> Optional[str]:
        try:
            r = self.session.get(url, timeout=20)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def extract(self, url: str) -> IPOData:
        html = self._fetch(url)
        if not html:
            return IPOData(url=url, extracted_at=datetime.now().strftime("%Y-%m-%d %H:%M"))

        tables = pd.read_html(StringIO(html), flavor="bs4")
        data = IPOData(url=url, extracted_at=datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Company name
        m = re.search(r'<title>([^|]+)', html, re.I)
        data.company_name = self._clean_text(m.group(1).replace(" IPO", "")) if m else "Unknown"
        data.company_name = data.company_name.replace("Date,", "")
        data.company_name = data.company_name[:21]
        # Issue price (cleaned)
        m = re.search(r'(?:Final )?Issue Price.*?([₹\d,.\s]+(?: to [₹\d,.\s]+)? per share)', html, re.I)
        if m:
            price = self._clean_amount_text(m.group(1))
            data.issue_price_per_share = price if price and "declared" not in price.lower() else "To be declared"

        # GMP
        m = re.search(r'Grey Market Premium.*?([₹\d,.\s]+)', html, re.I)
        if m:
            gmp_val = self._clean_amount_text(m.group(1))
            date = re.search(r'as of ([A-Za-z]+\s+\d{1,2},?\s+\d{4})', html, re.I)
            data.gmp = f"{gmp_val} (as of {date.group(1) if date else 'recent'})"

        # Timeline (enhanced robustness)
        timeline = {
            "open": r'(?:IPO Open|Opening|Bid/Offer Opens on).*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            "close": r'(?:IPO Close|Closing|Bid/Offer Closes on).*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            "allotment": r'(?:Tentative )?Allotment.*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            "refund": r'(?:Initiation of )?Refund.*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            "credit": r'Credit of Shares.*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            "listing": r'(?:Tentative )?Listing.*?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        }
        data.ipo_timeline = {}
        for k, pat in timeline.items():
            m = re.search(pat, html, re.I)
            if m:
                data.ipo_timeline[k] = self._clean_text(m.group(1))

        # IPO Details (improved regexes to target precise values from intro paragraph where available)
        details = {
            "issue_size": r'(?:Total )?Issue Size.*?([₹\d,.\s]+ (?:Cr|crores?))',
            "face_value": r'Face Value.*?₹?\s*([\d,]+\.?\d*)\s*per share',
            "fresh_issue": r'fresh issue.*?crore shares aggregating to (₹[\d.,]+)\s*(?:crores?)',
            "offer_for_sale": r'offer for sale.*?crore shares aggregating to (₹[\d.,]+)\s*(?:crores?)',
        }
        data.ipo_details = {}
        for k, pat in details.items():
            m = re.search(pat, html, re.I)
            if m:
                data.ipo_details[k] = self._extract_amount(m.group(1))

        # Fallback for issue_size if not matched (e.g., from table)
        if "issue_size" not in data.ipo_details:
            m = re.search(r'Issue Size.*?agg\.?\s*up to\s*([₹\d,.\s]+ Cr)', html, re.I)
            if m:
                data.ipo_details["issue_size"] = self._extract_amount(m.group(1))

        # print(data.ipo_details)
        try:
            data.ipo_details["offer_for_sale"] = float(data.ipo_details["issue_size"]) - float(
                data.ipo_details["fresh_issue"])
        except Exception as e:
            # print(e)
            data.ipo_details["offer_for_sale"] = "0"
            try:
                data.ipo_details["fresh_issue"] = float(data.ipo_details["issue_size"])
            except:
                data.ipo_details["fresh_issue"] = "0"

        # print(data.ipo_details)

        # Anchor Allocation
        m = re.search(r'Anchor Investor Shares Offered.*?(\d+)', html, re.I)
        if m:
            shares = self._clean_amount_text(m.group(1))
            data.anchor_allocation = 1 if shares and int(shares) > 0 else "No"
        else:
            data.anchor_allocation = 0

        # Financials (only March data)
        fin = {}
        for df in tables:
            if df.empty or df.shape[1] < 2:
                continue
            years = [str(c).strip().lower() for c in df.columns[1:]]

            # Extract rows
            rows = {
                "assets": ["assets", "total assets"],
                "total_income": ["total income", "revenue from operations", "total revenue"],
                "profit_after_tax": ["profit after tax", "pat", "net profit"],
                "net_worth": ["net worth"],
                "ebitda": ["ebitda"],
                "total_borrowings": ["total borrowing", "borrowing", "total borrowings"],
            }

            for label, kw in rows.items():
                if label in fin:
                    continue
                for _, row in df.iterrows():
                    cell = str(row.iloc[0]).lower()
                    if any(k in cell for k in kw):
                        vals = [self._clean_number(v) for v in row.iloc[1:]]
                        full_dict = {y: v for y, v in zip(years, vals) if v is not None}
                        # Filter only 'mar' data
                        fin[label] = {k.upper(): v for k, v in full_dict.items() if 'mar' in k}
                        break

            # Robust Borrowings calculation if not found
            if "total_borrowings" not in fin or not fin["total_borrowings"]:
                lt = next((r for _, r in df.iterrows() if "long term" in str(r.iloc[0]).lower()), None)
                st = next((r for _, r in df.iterrows() if "short term" in str(r.iloc[0]).lower()), None)
                if lt or st:
                    ltv = [self._clean_number(v) for v in (lt.iloc[1:] if lt else [0] * len(years))]
                    stv = [self._clean_number(v) for v in (st.iloc[1:] if st else [0] * len(years))]
                    total = [round(l + s, 2) for l, s in zip(ltv, stv)]
                    fin["total_borrowings"] = {y.upper(): v for y, v in zip(years, total) if v > 0}

        data.financials = {k: v for k, v in fin.items() if v}

        # Ratios (enhanced for KPI extraction)
        ratios = {"eps": {}, "pe_ratio": "N/A", "ronw_percent": {}, "roe": {}, "roce": {}, "debt_equity": {},
                  "pat_margin": {}, "ebitda_margin": {}}
        for df in tables:
            if df.empty or df.shape[1] < 2:
                continue
            txt = df.to_string().lower()
            if any(term in txt for term in
                   ["pre", "post", "eps", "p/e", "kpi", "key performance", "ronw", "roe", "roce", "debt", "pat margin",
                    "ebitda margin"]):
                for _, row in df.iterrows():
                    desc = str(row.iloc[0]).lower()
                    if df.shape[1] > 2 and ("pre" in txt or "post" in txt):
                        pre = self._clean_number(row.iloc[1]) if len(row) > 1 else None
                        post = self._clean_number(row.iloc[2]) if len(row) > 2 else None
                        val = pre  # Default to pre for single value KPIs
                    else:
                        val = self._clean_number(row.iloc[1]) if len(row) > 1 else None
                        pre = post = None

                    if "eps" in desc:
                        if pre: ratios["eps"]["Pre"] = pre
                        if post: ratios["eps"]["Post"] = post
                    if "p/e" in desc or "pe ratio" in desc:
                        p = []
                        if pre: p.append(f"{pre}x")
                        if post: p.append(f"{post}x")
                        ratios["pe_ratio"] = ", ".join(p) if p else "N/A"
                    if "ronw" in desc or "return on net worth" in desc and val:
                        ratios["ronw_percent"]["Latest"] = val
                    if "roe" in desc or "return on equity" in desc and val:
                        ratios["roe"]["Latest"] = val
                    if "roce" in desc or "return on capital employed" in desc and val:
                        ratios["roce"]["Latest"] = val
                    if "debt" in desc and "equity" in desc and val:
                        ratios["debt_equity"]["Latest"] = val
                    if "pat margin" in desc and val:
                        ratios["pat_margin"]["Latest"] = val
                    if "ebitda margin" in desc and val:
                        ratios["ebitda_margin"]["Latest"] = val

        data.ratios = ratios

        # Lot size (cleaned)
        data.lot_size = {}
        for df in tables:
            if df.shape[1] < 4 or "lot" not in " ".join(map(str, df.columns)).lower():
                continue
            for _, row in df.iterrows():
                desc = str(row.iloc[0]).lower()
                lots = self._clean_number(row.iloc[1])
                shares = self._clean_number(row.iloc[2])
                amount = self._clean_amount_text(str(row.iloc[3])) if len(row) > 3 else ""
                if not lots or not shares:
                    continue

                if "retail" in desc:
                    key = "retail_max" if "max" in desc else "retail_min"
                elif "s-hni" in desc:
                    key = "s_hni_max" if "max" in desc else "s_hni_min"
                elif "b-hni" in desc:
                    key = "b_hni_min"
                else:
                    continue

                data.lot_size[key] = {"lots": int(lots), "shares": int(shares), "amount": amount}

        # Unit
        page = html.lower()
        if "million" in page:
            data.unit = "Millions"
        elif "lakh" in page:
            data.unit = "Lakhs"
        else:
            data.unit = "Crores"

        return data

