"""
Shared Google Sheet reader module to eliminate duplicated CSV parsing logic.
Used by trader_smws.py and fund_manager.py to read strategy signals from Google Sheets.
"""

import pandas as pd
import time
from typing import Optional


def get_strategy_signal_from_sheet(
    gid: int = 614695683,  # Default Google Sheet gid for strategy signals
    row: int = 23,        # Row containing the main strategy signal
    col: int = 4,         # Column containing the signal value (1-indexed)
    timeout: int = 60,    # Maximum time to wait for sheet to load
    delay: float = 2.0,   # Delay between polling attempts
    max_retries: int = 10   # Maximum number of retries
) -> Optional[float]:
    """
    Safely read a float value from Google Sheet CSV export.
    
    Args:
        gid: Google Sheet sheet ID (default uses strategy signals sheet)
        row: Row number containing the signal
        col: Column number containing the signal value
        timeout: Maximum total time to wait (seconds)
        delay: Delay between retries (seconds)
        max_retries: Maximum number of retry attempts
    
    Returns:
        Float value if successfully read, None if failed
    """
    url_template = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?gid={gid}&single=true&output=csv"
    url = url_template.format(gid=gid)
    
    for attempt in range(max_retries):
        try:
            df = pd.read_csv(url)
            if len(df) > row and len(df.columns) > col:
                value = str(df.iloc[row, col]).strip()
                if value and value.lower() not in ["nan", "loading...", "loading", "none", ""]:
                    try:
                        clean_num = value.replace('%', '').replace('x', '').replace(',', '').replace('₹', '').strip()
                        return float(clean_num)
                    except ValueError:
                        pass
            print(f"Attempt {attempt + 1}: No valid value found at row {row}, col {col}")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error reading Google Sheet: {e}")
        
        time.sleep(delay)
    
    print(f"Failed to read Google Sheet after {max_retries} attempts")
    return None