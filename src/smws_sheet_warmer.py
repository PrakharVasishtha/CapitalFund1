"""
smws_sheet_warmer.py
====================
Automated Google Sheet recalculation trigger for Systematic Market & Withdrawal Strategy (SMWS).

Google Sheets published to web freezes external and dynamic calculations (like GOOGLEFINANCE)
unless an active web session visits the spreadsheet page. This module launches a lightweight
headless Playwright session to touch the published HTML sheet, forcing Google's server-side
calculation engine to evaluate all formulas and populate live values.
"""

import time
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure src in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from logger_setup import get_logger

logger = get_logger("smws_sheet_warmer")

PUBHTML_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pubhtml"

_last_recalc_time = 0.0
_recalc_lock = asyncio.Lock() if hasattr(asyncio, "Lock") else None

async def async_recalculate_smws_sheet(force: bool = False, timeout_ms: int = 25000) -> Dict[str, Any]:
    """
    Asynchronously opens the published Google Sheet HTML in a headless Playwright browser,
    prompting Google's recalculation pipeline to execute.
    
    Throttled to run at most once every 30 seconds unless force=True.
    """
    global _last_recalc_time
    now = time.time()
    
    if not force and (now - _last_recalc_time) < 30:
        logger.info(f"Skipping sheet recalc: last run was {int(now - _last_recalc_time)}s ago (< 30s throttle).")
        return {"status": "throttled", "elapsed": now - _last_recalc_time, "success": True}

    logger.info("Triggering Google Sheet internal recalculation via headless Playwright session...")
    try:
        from playwright.async_api import async_playwright
        start_t = time.time()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(PUBHTML_URL, wait_until="domcontentloaded", timeout=timeout_ms)
                # Allow 3-4 seconds for Google Sheets client-side JS / backend sync to trigger formulas
                await asyncio.sleep(3.5)
                title = await page.title()
                logger.info(f"Successfully loaded Google Sheet page: '{title}' ({time.time() - start_t:.2f}s)")
            finally:
                await context.close()
                await browser.close()
        
        _last_recalc_time = time.time()
        return {
            "status": "success",
            "title": title,
            "duration": round(time.time() - start_t, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "success": True
        }
    except Exception as e:
        logger.warning(f"Error triggering sheet recalculation with Playwright: {e}")
        return {"status": "error", "error": str(e), "success": False}

def recalculate_smws_sheet(force: bool = False, timeout_ms: int = 25000) -> Dict[str, Any]:
    """
    Synchronous wrapper to trigger Google Sheet recalculation.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, async_recalculate_smws_sheet(force, timeout_ms))
                return future.result(timeout=timeout_ms / 1000 + 5)
        else:
            return loop.run_until_complete(async_recalculate_smws_sheet(force, timeout_ms))
    except Exception:
        return asyncio.run(async_recalculate_smws_sheet(force, timeout_ms))

if __name__ == "__main__":
    print("Testing SMWS Sheet Warmer...")
    res = recalculate_smws_sheet(force=True)
    print("Result:", res)
