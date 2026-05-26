import requests
import json

def get_ipo_indicative_price(symbol: str, exchange: str = "NSE"):
    exchange = exchange.upper()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bseindia.com/",
        "Origin": "https://www.bseindia.com",
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        if exchange == "NSE":
            # Your existing NSE code (works well)
            session.get("https://www.nseindia.com", timeout=10)
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"
            response = session.get(url, timeout=10)

            if response.status_code != 200:
                return {"error": f"NSE API failed: {response.status_code}"}

            data = response.json()
            preopen = data.get("preOpenMarket", {})

            return {
                "exchange": "NSE",
                "symbol": symbol.upper(),
                "indicative_price": preopen.get("IEP"),
                "final_price": preopen.get("finalPrice"),
                "total_buy_qty": preopen.get("totalBuyQuantity"),
                "total_sell_qty": preopen.get("totalSellQuantity"),
                "ato_buy_qty": preopen.get("atoBuyQty"),
                "ato_sell_qty": preopen.get("atoSellQty"),
                "last_update_time": preopen.get("lastUpdateTime"),
            }

        elif exchange == "BSE":
            # Better approach for BSE
            session.get("https://www.bseindia.com", timeout=10)  # Initialize session

            # Try the quote endpoint (more reliable for current price)
            url = f"https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w"
            params = {
                "scripcode": symbol,
                "flag": "0",
                "fromdate": "",
                "todate": "",
                "seriesid": ""
            }

            response = session.get(url, params=params, timeout=15)

            print("Status:", response.status_code)           # Debug
            print("Content preview:", response.text[:300])   # Debug

            if response.status_code != 200:
                return {"error": f"BSE API failed: {response.status_code}"}

            # Some endpoints return JSON wrapped strangely or need .text parsing
            try:
                data = response.json()
            except json.JSONDecodeError:
                return {
                    "error": "BSE returned non-JSON (likely blocked or wrong endpoint)",
                    "status": response.status_code,
                    "preview": response.text[:500]
                }

            # Parse the actual data structure (adjust keys based on real response)
            # The structure varies — you'll need to inspect `data`
            print(json.dumps(data, indent=2))  # For debugging

            return {
                "exchange": "BSE",
                "symbol": symbol,
                "raw_data": data  # Return full data for now
            }

        else:
            return {"error": "Exchange must be NSE or BSE"}

    except Exception as e:
        return {"error": str(e)}


# ================= Example Usage =================

if __name__ == "__main__":

    # NSE IPO stock
    #result = get_ipo_indicative_price("TATATECH", "NSE")
    result = get_ipo_indicative_price("500400", "BSE")

    print(json.dumps(result, indent=2))
