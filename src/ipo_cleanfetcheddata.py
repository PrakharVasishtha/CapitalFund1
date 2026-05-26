# chittorgarh_ipo_extractor.py
import re
import requests
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from IpoDataExtractor import ChittorgarhIPOExtractor, \
    IPOData  # Assume the extractor class is in a file named IpoDataExtractor3.py


def clean_ipo_data(ipo_data: IPOData) -> Dict[str, Any]:
    """Clean the extracted data before writing to Excel.

    - Company name: Limit to 15 characters (truncate with '...')
    - Dates: Format to ddmmyyyy (for extracted_at and timeline dates)
    - Flatten and clean numbers/strings as needed
    """
    flat_data = ipo_data.to_dict()

    # Clean company name (limit to 15 chars)
    if 'company_name' in flat_data:
        name = flat_data['company_name']
        flat_data['company_name'] = name[:24] if len(name) > 19 else name

    # Format extracted_at to ddmmyyyy
    if 'extracted_at' in flat_data:
        try:
            dt = datetime.strptime(flat_data['extracted_at'], "%Y-%m-%d %H:%M")
            flat_data['extracted_at'] = dt.strftime("%d%m%Y")
        except ValueError:
            pass  # Leave as is if format doesn't match

    # Format timeline dates to ddmmyyyy (e.g., 'December 16, 2025' -> '16122025')
    if 'ipo_timeline' in flat_data and isinstance(flat_data['ipo_timeline'], dict):
        formats = [
            "%B %d, %Y",  # December 5, 2025
            "%b %d, %Y",  # Dec 5, 2025
            "%d %B %Y",  # 5 December 2025
            "%d %b %Y",  # 5 Dec 2025
            "%Y-%m-%d",  # 2025-12-05 (ISO)
            "%d%m%Y"     # 05122025 (already formatted)
        ]
        for key, date_str in list(flat_data['ipo_timeline'].items()):  # Use list to avoid runtime change
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    flat_data['ipo_timeline'][key] = dt.strftime("%d%m%Y")
                    break
                except ValueError:
                    pass  # Try next format
            # If no format matches, leave original

    # Additional cleanings (examples):
    # - Truncate long strings (e.g., gmp to 20 chars)
    if 'gmp' in flat_data:
        flat_data['gmp'] = flat_data['gmp'][:20] + '...' if len(flat_data['gmp']) > 20 else flat_data['gmp']

    # - Ensure numbers are floats (already done in extractor, but reinforce)
    for key in ['financials', 'ratios']:
        if key in flat_data and isinstance(flat_data[key], dict):
            for sub_key, val in flat_data[key].items():
                if isinstance(val, dict):
                    for inner_key, inner_val in val.items():
                        if isinstance(inner_val, (int, float)):
                            flat_data[key][sub_key][inner_key] = float(inner_val)
    #print("Finished cleaning IPO data.")
    #print("flat_data:", flat_data)
    return flat_data


# ====================== EXAMPLE USAGE ======================
if __name__ == "__main__":
    extractor = ChittorgarhIPOExtractor()

    # Example: Extract from a URL
    #url = "https://www.chittorgarh.com/ipo/flywings-simulator-ipo/2396/"
    url = "https://www.chittorgarh.com/ipo/yajur-fibres-ipo/2128/"
    ipo_data = extractor.extract(url)

    clean_data=clean_ipo_data(ipo_data)
    #print(clean_data)