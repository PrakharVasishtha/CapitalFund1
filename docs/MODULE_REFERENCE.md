# CapitalFund1 — Module Reference Guide

This reference provides a complete technical catalog of all Python modules within `src/` and the root directory, detailing their responsibilities, key functions, input parameters, and interactions.

---

## 1. Orchestration, Scheduling & Base Framework

### [`src/common_schedule_all.py`](file:///d:/CapitalFund1/src/common_schedule_all.py)
- **Role**: Primary system orchestrator and 24/7 task daemon.
- **Key Functions**:
  - `run_threaded(job_func)`: Non-blocking scheduler engine. Executes every scheduled task in a dedicated background daemon thread with re-entrancy locking, ensuring time-critical market events (09:00 LC Sell, 09:32 IEP check, 10:01 Regular session) fire without being delayed by heavy network I/O.
  - `launch_streamlit_dashboard()`: Verifies if port 8501 is open via socket check; launches `dashboard.py` via `subprocess.Popen` if offline.
  - `run_now()`: Sequentially executes startup initialization, primes the SQLite dual-tier storage engine, and synchronizes `Master.xlsx`.
  - Daily schedules from `08:00` to `14:50` configured via the Python `schedule` module.
- **Dependencies**: `schedule`, `threading`, `database`, `common_foundation`, `common_master_functions`, `allotment_application_ipo`, `fund_manager`.

### [`src/database.py`](file:///d:/CapitalFund1/src/database.py)
- **Role**: High-performance SQLite Dual-Tier storage engine (`capitalfund.db`) operating in Write-Ahead Logging (`WAL`) mode.
- **Key Functions**:
  - `init_db()`: Initializes relational tables (`master_users`, `allotted_holdings`, `ipo_research`, `ipo_applied`) with indexes and WAL mode.
  - `import_all_from_excel()`: Safely ingests data from `Master.xlsx`, `allotted_holdings.xlsx`, `General.xlsx`, and `IPO-applied.xlsx` into SQLite.
  - `sync_all_to_excel()`: Exports SQLite tables back to Excel files via atomic `.tmp_<PID>` replacement, eliminating `PermissionError` file-locking issues.
  - `get_allotted_holdings()`, `update_holding_status()`: Non-blocking queries and state transitions for listing day trading.

### [`src/config.py`](file:///d:/CapitalFund1/src/config.py)
- **Role**: Centralized single source of truth for business constants, thresholds, and state-machine enums.
- **Key Constants & Classes**:
  - Capital reserves: `SME_IPO_FUND_RESERVE` (₹280,000), `MB_IPO_FUND_RESERVE` (₹209,000), `INSTANT_WITHDRAWAL_LIMIT` (₹200,000), `HNI_MINIMUM_THRESHOLD` (₹200,001).
  - Trading thresholds: `MAINBOARD_LOSS_CANCEL_THRESHOLD_PCT` (11.9%), `SME_DISCOUNT_CANCEL_THRESHOLD_PCT` (0.0%), `BUYER_SELLER_HIGH_DEMAND_RATIO` (60.0%).
  - Status enums: `SpecialSessionStatus` and `RegularSessionStatus`.

### [`src/Base.py`](file:///d:/CapitalFund1/src/Base.py)
- **Role**: Foundational utilities, security helpers, and atomic file safety handlers.
- **Key Functions**:
  - `load_credentials(file_path)`: Parses multi-user JSON array from the `CAPITALFUND_USERS` environment variable.
  - `safe_load_workbook(path, retries=5, delay=0.4)`: Loads openpyxl workbooks with exponential backoff to handle concurrent read/write locks.
  - `safe_save_workbook(wb, path)`: Performs atomic write using a temporary `.tmp_<PID>` file followed by atomic `os.replace()`.
  - `get_netbanking_otp_sms(EMAIL_USER, EMAIL_PASS, search_query)`: Intercepts SMS OTPs forwarded to Gmail via IMAP within a 2-minute expiration window.
  - `get_vix()`: Queries India VIX (`^INDIAVIX`) via `yfinance`.
  - `parse_float(val)`: Cleans strings containing currency symbols, commas, and percentage signs into standard floats.

### [`src/common_foundation.py`](file:///d:/CapitalFund1/src/common_foundation.py)
- **Role**: Centralized logging wrapper, email transmission, and Telegram bot notification engine.
- **Key Functions**:
  - `log_info(msg, function_name)`, `log_warning(msg, function_name)`, `log_error(msg, exc, function_name)`: Standard structured logging with formatted timestamps and filenames.
  - `send_telegram_notification(msg, parse_mode="HTML")`: Sends instant mobile alerts to Telegram chat using the Bot API with HTML formatting.
  - `send_email(email_to, sub_send, content_send)`: Sends Gmail alerts over SMTP (port 587/465).
  - `send_email_with_excel(mail_subject, mail_content, path_of_file, email_to)`: Attaches updated Excel workbooks to alert emails.
  - `internetcheck()`: Blocks execution until internet connectivity is established.

### [`src/logger_setup.py`](file:///d:/CapitalFund1/src/logger_setup.py)
- **Role**: Advanced logging configuration with rotating file handlers and custom log levels.
- **Key Handlers**:
  - Console: `INFO` level.
  - `capitalfund.log`: `INFO`+, TimedRotatingFileHandler (midnight, 30-day retention).
  - `errors.log`: `ERROR`+ file handler.
  - `audit.log`: Dedicated handler for custom level `AUDIT = 25`.
- **Key Function**: `get_logger(name)` returns named logger instances.

---

## 2. IPO Research, Extraction & Scoring Pipeline

### [`src/ipo_scraper.py`](file:///d:/CapitalFund1/src/ipo_scraper.py) & [`src/IpoDataExtractor.py`](file:///d:/CapitalFund1/src/IpoDataExtractor.py)
- **Role**: Scrapes Chittorgarh IPO listing pages.
- **Key Classes & Methods**:
  - `ChittorgarhIPOExtractor.extract(url)`: Extracts structured data into `IPOData` dataclass.
  - `page_contains_trust(url)`: Discards REITs and InvITs.

### [`src/ipo_ExtractGMP.py`](file:///d:/CapitalFund1/src/ipo_ExtractGMP.py)
- **Role**: Scrapes live Grey Market Premium (GMP) tables, returning GMP in ₹ and GMP as a percentage of issue price.

### [`src/ipo_ExtractSubscription.py`](file:///d:/CapitalFund1/src/ipo_ExtractSubscription.py)
- **Role**: Scrapes live subscription metrics across Retail, QIB, and NII categories.

### [`src/ipo_ExtractReview.py`](file:///d:/CapitalFund1/src/ipo_ExtractReview.py) & [`src/ipo_pe.py`](file:///d:/CapitalFund1/src/ipo_pe.py)
- **Role**: Parses analyst recommendations (Apply / Neutral / Avoid) and extracts Price-to-Earnings ratios.

### [`src/ipo_write_formula.py`](file:///d:/CapitalFund1/src/ipo_write_formula.py) & [`src/ipo_formula.py`](file:///d:/CapitalFund1/src/ipo_formula.py)
- **Role**: Writes dynamic Excel formulas into `General.xlsx` calculating composite IPO scores and assigning Apply Priority (`1`, `2`, `3`).

### [`src/ipo_excel_manager.py`](file:///d:/CapitalFund1/src/ipo_excel_manager.py) & [`src/ipo_excel_3pm.py`](file:///d:/CapitalFund1/src/ipo_excel_3pm.py)
- **Role**: Controls row additions, deduplication, and 3 PM pre-close subscription updates.

### [`src/ipo_listing_result.py`](file:///d:/CapitalFund1/src/ipo_listing_result.py)
- **Role**: Scheduled at 10:05 AM on listing day. Scrapes actual listing opening price from Chittorgarh and records binary success (`1` = Gain, `0` = Discount) in Column 4 of `General.xlsx`.

---

## 3. Fund Management & Bank-Broker Routing

### [`src/fund_manager.py`](file:///d:/CapitalFund1/src/fund_manager.py)
- **Role**: Assesses portfolio cash needs for closing IPOs and triggers automated broker-to-bank capital withdrawals.
- **Key Functions**:
  - `ipo_required_fund(d)`: Calculates total funds required across Day 0 and Day 1 closing IPOs.
  - `daily_money_withdraw()`: Queries Kotak bank balance, compares against required funds, and triggers `withdraw_from_zerodha()`.

### [`src/fund_zerodha_withdraw.py`](file:///d:/CapitalFund1/src/fund_zerodha_withdraw.py)
- **Role**: Automated Playwright script that logs into Zerodha Console (`console.zerodha.com`), submits withdrawal requests for the calculated deficit, and logs audit events.

### [`src/fund_bank_to_kite.py`](file:///d:/CapitalFund1/src/fund_bank_to_kite.py) & [`src/fund_transfer_for_smws.py`](file:///d:/CapitalFund1/src/fund_transfer_for_smws.py)
- **Role**: Sweeps excess/idle Kotak Bank cash into Zerodha Kite for ETF trading when no IPO allocations are pending.

### [`src/fund_kotak_get_balance.py`](file:///d:/CapitalFund1/src/fund_kotak_get_balance.py)
- **Role**: Asynchronous Playwright routine to log into Kotak Mahindra NetBanking, bypass 2FA via SMS OTP extraction, and return the real-time savings account balance.

---

## 4. Systematic ETF Strategy (SMWS)

### [`src/strategy_sheet.py`](file:///d:/CapitalFund1/src/strategy_sheet.py)
- **Role**: Connects to the published Google Sheet CSV feed to extract strategy signals for index and commodity ETFs.
- **Key Function**: `get_strategy_signal_from_sheet(gid, row, col)`: Polls published CSV endpoints with retries and exponential delay.

### [`src/trader_smws.py`](file:///d:/CapitalFund1/src/trader_smws.py)
- **Role**: Core execution engine for buying and selling SMWS ETFs (`NIFTYIETF`, `TATAGOLD`, `TATSILV`).
- **Key Functions**:
  - `smws_buyer()`: Evaluates buy signals, calculates per-security capital slices, and places buy orders.
  - `smws_seller()`: Evaluates sell signals and liquidates designated ETF positions.

### [`src/trader_priority_ipo_smws_sell.py`](file:///d:/CapitalFund1/src/trader_priority_ipo_smws_sell.py)
- **Role**: Emergency liquidity provider. Liquidates SMWS ETF holdings if immediate capital is needed for high-priority closing IPO applications.

### [`src/trader_zerodha_buy.py`](file:///d:/CapitalFund1/src/trader_zerodha_buy.py) & [`src/trader_zerodha_sell.py`](file:///d:/CapitalFund1/src/trader_zerodha_sell.py)
- **Role**: Browser-driven order placement handlers for Zerodha Kite. Emits `AUDIT` log entries upon successful execution.

### [`src/trader_zerodha_base.py`](file:///d:/CapitalFund1/src/trader_zerodha_base.py)
- **Role**: Handles Zerodha Kite login, 2FA TOTP verification, and fetches real-time available margin balances.

---

## 5. Allotment Management & IPO Application

### [`src/allotment_application_ipo.py`](file:///d:/CapitalFund1/src/allotment_application_ipo.py)
- **Role**: Scans `General.xlsx` for IPOs closing today, ranks them by priority (`3`, `2`, `1`), and triggers multi-account ASBA applications.

### [`src/allotment_kotak_ipo_apply.py`](file:///d:/CapitalFund1/src/allotment_kotak_ipo_apply.py)
- **Role**: Asynchronous Playwright routine automating Kotak NetBanking ASBA applications.
- **Key Capabilities**:
  - Automatically calculates HNI lot size ($\ge \text{₹}200,001$) or Retail lot size.
  - Uses fuzzy matching to select the correct IPO name in the Kotak dropdown.
  - Enters Demat / PAN details and submits the application.

### [`src/allotment_general.py`](file:///d:/CapitalFund1/src/allotment_general.py) & [`src/allotment_fetch.py`](file:///d:/CapitalFund1/src/allotment_fetch.py)
- **Role**: Scans multi-account Zerodha portfolios, discovers newly allotted IPO shares, and filters out non-IPO ETF holdings.

### [`src/allotment_update.py`](file:///d:/CapitalFund1/src/allotment_update.py)
- **Role**: Registers new allotments in `allotted_holdings.xlsx`, enriches records with lot sizes and issue prices, and initializes status codes (`special_session_status = 5`).

---

## 6. Listing Day Selling Strategies

### [`src/ss_sale_order_on_lc_on_start_of_ss.py`](file:///d:/CapitalFund1/src/ss_sale_order_on_lc_on_start_of_ss.py)
- **Role**: Scheduled at 09:00 AM on listing day. Places Lower Circuit (LC) sell orders on Zerodha Kite for all newly allotted shares (`status == 5`).

### [`src/special_sesion_zerodha_sell.py`](file:///d:/CapitalFund1/src/special_sesion_zerodha_sell.py)
- **Role**: Executes the pre-open market/limit sell order submission and handles order cancellation requests (`zerodha_cancel_order()`).

### [`src/ss_Before_session_close_cancel_sale_or_not.py`](file:///d:/CapitalFund1/src/ss_Before_session_close_cancel_sale_or_not.py)
- **Role**: Scheduled at 09:32 AM. Fetches Indicative Equilibrium Prices (IEP).
- **Rule Engine**:
  - Mainboard: Cancels sell order if $\text{Loss} > 11.9\%$.
  - SME: Cancels sell order if $\text{Loss} > 0\%$.
  - Updates `special_session_status` and hands unexecuted shares over to `regular_session_status = 1`.

### [`src/special_session_indicative_price_nse.py`](file:///d:/CapitalFund1/src/special_session_indicative_price_nse.py) & [`src/special_session_indicative_price_bse.py`](file:///d:/CapitalFund1/src/special_session_indicative_price_bse.py)
- **Role**: Queries NSE and BSE pre-open discovery feeds to retrieve live indicative prices and market equilibrium volumes.

### [`src/regular_session_sell.py`](file:///d:/CapitalFund1/src/regular_session_sell.py)
- **Role**: Scheduled at 10:01 AM for shares entering the normal market session.
- **Rule Engine**:
  - Analyzes market depth: Computes $\text{Buyer Ratio} = \text{Buy Qty} / (\text{Buy Qty} + \text{Sell Qty})$.
  - If Ratio $\ge 60\%$: Monitors for Upper Circuit (UC) for 30 minutes. If UC locked, holds. If no UC after 30 min, places 2 GTT orders (+2% / +5%).
  - If Ratio $< 60\%$: Places immediate defensive GTT orders (+0.5% / +1.0%).

---

## 7. Master Synchronization & Dashboard

### [`src/master_excel_manager.py`](file:///d:/CapitalFund1/src/master_excel_manager.py)
- **Role**: Synchronizes `Master.xlsx` ('Users' worksheet) with `.env` credentials and updates real-time portfolio valuations.

### [`src/ipo_applied_manager.py`](file:///d:/CapitalFund1/src/ipo_applied_manager.py)
- **Role**: Appends submitted application records (IPO Name, Shares Applied, Issue Price, Application Amount) to per-user sheets in `IPO-applied.xlsx`.

### [`dashboard.py`](file:///d:/CapitalFund1/dashboard.py)
- **Role**: Enterprise Streamlit Control Hub providing real-time KPI metrics, active allotment monitors, IPO research exploration, SMWS signals, and one-click manual task triggers.
