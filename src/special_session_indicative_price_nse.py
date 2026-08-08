"""
special_session_indicative_price_nse.py
========================================
Fetches listing day pre-open / indicative equilibrium price (IEP) for IPO stocks on NSE or BSE.
"""
import requests
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from special_session_indicative_price_bse import ipo_indicative_price_bse


def get_ipo_indicative_price(symbol: str, exchange: str = "NSE") -> dict:
    """
    Fetches pre-open / indicative price data for a symbol on NSE or BSE.

    Returns a dict:
      {
        "exchange": "NSE" | "BSE",
        "symbol": str,
        "indicative_price": float,
        "final_price": float or None,
        "total_buy_qty": int or None,
        "total_sell_qty": int or None,
        "ato_buy_qty": int or None,
        "ato_sell_qty": int or None,
        "last_update_time": str or None,
        "error": str or None
      }
    """
    exchange_upper = exchange.upper().strip() if exchange else "NSE"
    symbol_upper = symbol.upper().strip() if symbol else ""

    if exchange_upper == "NSE":
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.nseindia.com/",
        }

        session = requests.Session()
        session.headers.update(headers)

        try:
            # 1. Establish session cookies with NSE
            session.get("https://www.nseindia.com", timeout=10)

            # 2. Query NSE pre-open market data endpoint
            url = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"
            response = session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json().get("data", [])
                for item in data:
                    meta = item.get("metadata", {})
                    if meta.get("symbol", "").upper() == symbol_upper:
                        detail = item.get("detail", {}).get("preOpenMarket", {})
                        iep = detail.get("IEP") or meta.get("iep") or meta.get("lastPrice")
                        return {
                            "exchange": "NSE",
                            "symbol": symbol_upper,
                            "indicative_price": float(iep) if iep is not None else 0.0,
                            "final_price": detail.get("finalPrice"),
                            "total_buy_qty": detail.get("totalBuyQuantity"),
                            "total_sell_qty": detail.get("totalSellQuantity"),
                            "ato_buy_qty": detail.get("atoBuyQty"),
                            "ato_sell_qty": detail.get("atoSellQty"),
                            "last_update_time": detail.get("lastUpdateTime"),
                            "error": None
                        }

            # 3. Fallback attempt using curl_cffi for direct quote API
            try:
                from curl_cffi import requests as c_requests
                csession = c_requests.Session(impersonate="chrome120")
                csession.headers.update({"Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol_upper}"})
                csession.get("https://www.nseindia.com", timeout=10)
                res2 = csession.get(f"https://www.nseindia.com/api/quote-equity?symbol={symbol_upper}", timeout=10)
                if res2.status_code == 200:
                    qdata = res2.json()
                    preopen = qdata.get("preOpenMarket", {})
                    iep = preopen.get("IEP")
                    return {
                        "exchange": "NSE",
                        "symbol": symbol_upper,
                        "indicative_price": float(iep) if iep is not None else 0.0,
                        "final_price": preopen.get("finalPrice"),
                        "total_buy_qty": preopen.get("totalBuyQuantity"),
                        "total_sell_qty": preopen.get("totalSellQuantity"),
                        "ato_buy_qty": preopen.get("atoBuyQty"),
                        "ato_sell_qty": preopen.get("atoSellQty"),
                        "last_update_time": preopen.get("lastUpdateTime"),
                        "error": None
                    }
            except Exception:
                pass

            return {
                "exchange": "NSE",
                "symbol": symbol_upper,
                "indicative_price": 0.0,
                "error": f"Symbol '{symbol_upper}' not found in pre-open data"
            }

        except Exception as e:
            return {
                "exchange": "NSE",
                "symbol": symbol_upper,
                "indicative_price": 0.0,
                "error": str(e)
            }

    elif exchange_upper == "BSE":
        try:
            bse_price = ipo_indicative_price_bse(symbol, exchange="BSE")
            return {
                "exchange": "BSE",
                "symbol": symbol_upper,
                "indicative_price": float(bse_price) if bse_price else 0.0,
                "error": None
            }
        except Exception as e:
            return {
                "exchange": "BSE",
                "symbol": symbol_upper,
                "indicative_price": 0.0,
                "error": str(e)
            }

    else:
        return {
            "exchange": exchange_upper,
            "symbol": symbol_upper,
            "indicative_price": 0.0,
            "error": "Exchange must be NSE or BSE"
        }


if __name__ == "__main__":
    res = get_ipo_indicative_price("IDEALTECHO", "NSE")
    print(json.dumps(res, indent=2))
