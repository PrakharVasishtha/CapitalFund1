# CapitalFund1 — IPO Automation & Trading System

An automated system for managing IPO research, fund allocation, SMWS (Systematic Market & Withdrawal Strategy) trading, and allotment tracking across multiple Zerodha accounts, backed by Kotak bank integration.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Credentials Configuration](#credentials-configuration)
- [Daily Schedule](#daily-schedule)
- [Key Modules](#key-modules)
- [Excel Files](#excel-files)
- [Status Codes](#status-codes)
- [Running the System](#running-the-system)
- [Sample Terminal Run Outputs](#sample-terminal-run-outputs)
- [Adding a New Account](#adding-a-new-account)
- [Mobile SMS Forwarding](#mobile-sms-forwarding)

---

## Overview

CapitalFund1 automates the full lifecycle of IPO investing across multiple broker accounts:

1. **Scrapes** new IPO listings from Chittorgarh daily.
2. **Evaluates** each IPO using GMP (Grey Market Premium), subscription data, analyst reviews, and India VIX.
3. **Applies** to shortlisted IPOs via Kotak bank UPI.
4. **Manages funds** by withdrawing from Zerodha to Kotak bank as required, and transferring idle bank funds to Zerodha.
5. **Trades SMWS** (NIFTYIETF, TATAGOLD, TATSILV) based on a live strategy Google Sheet.
6. **Detects new allotments** after IPO listing by logging into each Zerodha account and scanning Holdings.
7. **Tracks allotments** in `allotted_holdings.xlsx` and updates enrichment data (GMP, subscription, review, VIX).

---

## Project Structure

```
CapitalFund1/
├── src/
│   ├── common_schedule_all.py              # Main scheduler -- entry point, runs 24/7
│   ├── common_master_functions.py          # IPO scraping, data entry, 3pm updates
│   ├── common_foundation.py                # Logging, email, internet check utilities
│   │
│   ├── allotment_general.py                # Orchestrates new allotment detection
│   ├── allotment_fetch.py                  # Logs into Zerodha, detects non-default holdings
│   ├── allotment_update.py                 # Updates allotted_holdings.xlsx with enrichment data
│   ├── allotment_application_ipo.py        # Determines which IPOs to apply to on close date
│   ├── allotment_kotak_ipo_apply.py        # Automates Kotak UPI IPO application
│   │
│   ├── fund_manager.py                     # Calculates required IPO funds, triggers Zerodha withdrawal
│   ├── fund_transfer_for_smws.py           # Transfers idle bank balance to Zerodha for SMWS
│   ├── fund_bank_to_kite.py                # Playwright: Kotak bank to Zerodha fund transfer
│   ├── fund_kotak_get_balance.py           # Async: Fetches current Kotak bank balance via OTP
│   ├── fund_zerodha_withdraw.py            # Playwright: Zerodha to Kotak bank withdrawal
│   │
│   ├── trader_smws.py                      # SMWS buyer & seller (NIFTYIETF, TATAGOLD, TATSILV)
│   ├── trader_priority_ipo_smws_sell.py    # Sells SMWS when IPO funds are required
│   ├── trader_zerodha_buy.py               # Playwright: Buys ETF on Zerodha Kite
│   ├── trader_zerodha_sell.py              # Playwright: Sells ETF on Zerodha Kite
│   ├── trader_zerodha_base.py              # Playwright: Fetches Zerodha portfolio balance
│   │
│   ├── special_sesion_zerodha_sell.py      # Sells on BSE special pre-open session
│   ├── special_session_monitor.py          # Monitors indicative prices, triggers special sell
│   ├── special_session_indicative_price_nse.py
│   ├── special_session_indicative_price_bse.py
│   │
│   ├── ipo_scraper.py                      # Fetches latest IPO listings from Chittorgarh
│   ├── IpoDataExtractor.py                 # Extracts detailed IPO data from listing page
│   ├── ipo_cleanfetcheddata.py             # Cleans and normalizes raw IPO data
│   ├── ipo_excel_manager.py                # Reads/writes IPO data to General.xlsx
│   ├── ipo_excel_3pm.py                    # Updates IPO rows at 3pm close
│   ├── ipo_ExtractGMP.py                   # Scrapes Grey Market Premium
│   ├── ipo_ExtractReview.py                # Checks for negative analyst review keywords
│   ├── ipo_ExtractSubscription.py          # Scrapes live and final subscription data
│   ├── ipo_formula.py / ipo_write_formula.py
│   ├── ipo_base.py / ipo_base_pe.py / ipo_pe.py
│   │
│   ├── Base.py                             # Shared utilities: credentials, Excel helpers, VIX
│   └── common_mn_otp_zrdh.py              # OTP extraction utility for Zerodha
│
├── allotted_holdings.xlsx                  # Per-user allotment tracking workbook
├── General.xlsx                            # Main IPO research database
├── Master.xlsx                             # Master reference data
├── requirements.txt                        # Python dependencies
├── .env                                    # Secret credentials (gitignored)
└── README.md
```

---

## Setup

### 1. Install Dependencies

```powershell
cd d:\CapitalFund1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Credentials

Create a `.env` file in the project root (never commit this file):

```env
CAPITALFUND_USERS='[
  {
    "uci": "1",
    "name": "Account Holder Name",
    "broker_client_id": "ZR1234",
    "password_broker": "yourpassword",
    "topt_broker": "TOTP_BASE32_SECRET",
    "bank_user": "kotak_user_id",
    "bank_password": "kotak_password",
    "email_user": "gmail@gmail.com",
    "email_password": "gmail_app_password"
  }
]'
```

> **Note:** `topt_broker` is the base32 TOTP secret (not the 6-digit OTP).
> Find it when setting up 2FA in Zerodha — save the secret key before scanning the QR code.

### 3. Gmail App Password

For email alerts and OTP forwarding, you need a Gmail App Password:
1. Enable 2-Factor Authentication: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Use this App Password as `email_password` in `.env`

---

## Credentials Configuration

| Field              | Description                                       |
|--------------------|---------------------------------------------------|
| `uci`              | Unique Client Identifier (sheet name in Excel)    |
| `name`             | Human-readable account name                       |
| `broker_client_id` | Zerodha client ID (e.g. `ZR1234`)                 |
| `password_broker`  | Zerodha login password                            |
| `topt_broker`      | TOTP base32 secret for Zerodha 2FA                |
| `bank_user`        | Kotak bank user ID                                |
| `bank_password`    | Kotak bank password                               |
| `email_user`       | Gmail address (receives Kotak OTP SMS forwards)   |
| `email_password`   | Gmail App Password                                |

---

## Daily Schedule

| Time    | Task                   | Description                                                             |
|---------|------------------------|-------------------------------------------------------------------------|
| Startup | `run_now()`            | Runs all tasks once immediately on script start                         |
| 08:30   | `ipo_entry()`                  | Scrapes new IPOs and appends them to `General.xlsx`                     |
| 08:40   | `allotment_general()`          | Checks Zerodha holdings for new IPO allotments and updates tracker      |
| 09:00   | `special_session_monitoring()` | Monitors listing day pre-open indicative prices & places sell orders   |
| 09:02   | `money_withdraw()`             | Calculates required IPO funds, withdraws from Zerodha to Kotak          |
| 09:09   | `bank_to_kite()`       | Transfers excess idle bank balance to Zerodha Kite for SMWS trading     |
| 09:18   | `smws_seller()`        | Sells SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on strategy sheet |
| 09:18   | `priority_ipo_sell()`  | Sells SMWS specifically when IPO fund is required                       |
| 09:25   | `smws_buyer()`         | Buys SMWS ETFs based on strategy Google Sheet signals                   |
| 10:05   | `update_before_close()`| Updates IPO data in `General.xlsx`                                      |
| 14:50   | `update_before_close()`| Pre-close 3pm data refresh                                              |
| 14:55   | `ipo_application()`    | Applies to IPOs closing today via Kotak UPI                             |
| 15:05   | `update_before_close()`| Final post-close update                                                 |

---

## Key Modules

### `common_schedule_all.py`
Main entry point. Runs `run_now()` on startup and uses the `schedule` library to trigger daily tasks. Runs as an infinite loop (`while True: schedule.run_pending()`).

### `allotment_general.py`
Orchestrates allotment detection. For each user, calls `fetch_allotment_holdings()` to check Zerodha Holdings for any non-default stocks. If found, calls `excel_holdings()` to register and enrich them.

### `allotment_fetch.py`
Logs into each Zerodha Kite account via Playwright, navigates to Holdings, and extracts all holding symbols. Filters out:
- Default SMWS holdings: `NIFTYIETF`, `TATAGOLD`, `TATSILV`
- Market index tickers: `NIFTY 50`, `SENSEX`, `BANKNIFTY`, etc.

Returns the symbol(s) of any newly allotted IPO stocks.

### `allotment_update.py` — `excel_holdings(usr_id, holding_symbol)`
- Resolves `allotted_holdings.xlsx` path dynamically (works from any working directory).
- If `holding_symbol` is new, appends a row with `special_session_status = 5`.
- Scans all rows with status `5` and fetches GMP, subscription, analyst review, and India VIX.
- Saves enriched data to the corresponding columns.

### `fund_manager.py` — `daily_money_withdraw()`
1. Reads `General.xlsx` for IPOs closing today and tomorrow.
2. Calculates total funds required (SME: ₹2,80,000/IPO; MB: ₹2,09,000/IPO).
3. Fetches current Kotak bank balance.
4. If Zerodha funds are needed, initiates withdrawal via Playwright.

### `trader_smws.py`
Reads a live Google Sheet (published as CSV) to determine buy/sell signals for `NIFTYIETF`, `TATAGOLD`, and `TATSILV`. Executes buy/sell orders via Playwright on Zerodha Kite.

### `allotment_application_ipo.py` — `ipo_application()`
Checks `General.xlsx` for IPOs with close date = today and apply flag set. Submits UPI applications through Kotak in priority order (category 3 → 2 → 1).

---

## Excel Files

### `General.xlsx`
Main IPO research database. Contains two sheets:
- `IPOSME` — SME IPO data
- `IPOMB` — Mainboard IPO data

Key columns (1-indexed):
| Column | Field                       |
|--------|-----------------------------|
| 2      | IPO Name                    |
| 40     | Close Date (day of month)   |
| 42     | Apply flag (`0`/`1`/`2`/`3`)|

### `allotted_holdings.xlsx`
Per-user allotment tracking. Each user has a sheet named by their `uci` (e.g., `"1"`). Row 1 is the header row.

| Column | Field                        |
|--------|------------------------------|
| 1      | `security_name`              |
| 2      | `lot_size`                   |
| 3      | `issue_price`                |
| 4      | `shares_allocated`           |
| 5      | `lots_issued`                |
| 6      | `exchange`                   |
| 7      | `special_session_status`     |
| 8      | `regular_session_monitoring` |
| 9      | `regular_session_day`        |
| 10     | `regular_session_status`     |
| 23     | Review score                 |
| 24     | Subscription - Retail        |
| 25     | Subscription - NII           |
| 26     | Subscription - QIB           |
| 28     | GMP (Grey Market Premium)    |
| 35     | India VIX                    |

---

## Status Codes

### `special_session_status` (Column 7 of `allotted_holdings.xlsx`)

| Value | Meaning                                      |
|-------|----------------------------------------------|
| `0`   | Not started                                  |
| `1`   | Special session sell started                 |
| `2`   | Sold in special pre-open session             |
| `3`   | Not sold in special session                  |
| `5`   | Empty / pending enrichment (newly added row) |

### `regular_session_status` (Column 10 of `allotted_holdings.xlsx`)

| Value | Meaning                                |
|-------|----------------------------------------|
| `0`   | Not started                            |
| `1`   | Regular session sell started           |
| `2`   | Sold in regular session                |
| `3`   | Not sold in regular session            |
| `4`   | Transferred to UC/LC monitor           |

### IPO apply flag (Column 42 of `General.xlsx`)

| Value | Meaning                                   |
|-------|-------------------------------------------|
| `0`   | Do not apply                              |
| `1`   | Apply only if SMWS strategy is inactive   |
| `2`   | Apply (normal priority)                   |
| `3`   | Apply (high priority)                     |

---

## Running the System

### Start the Scheduler (runs all day)
```powershell
cd d:\CapitalFund1
.venv\Scripts\python.exe src\common_schedule_all.py
```

### Auto-start at 8:30 AM via Windows Task Scheduler
```powershell
schtasks /create /tn "CapitalFund_Scheduler" /tr "d:\CapitalFund1\.venv\Scripts\python.exe d:\CapitalFund1\src\common_schedule_all.py" /sc daily /st 08:30
```

### Run Allotment Detection Manually
```powershell
.venv\Scripts\python.exe src\allotment_general.py
```

---

## Sample Terminal Run Outputs

### 1. Allotment Detection Scanner (`allotment_general.py`)

When running allotment scan across user accounts:

```text
PS D:\CapitalFund1> .venv\Scripts\python.exe src\allotment_general.py
-----------ipo_allotment_manager----------
______fetch_allotment_holdings___ ZR1234
Other holdings found for ZR1234: ['TATATECH']
Allotment found for 1: ['TATATECH']
excel_holdings 1
Processing row 2: TATATECH
excel_holdings: Successfully updated details for row 2 (TATATECH)
```

If no new allotment is present:

```text
PS D:\CapitalFund1> .venv\Scripts\python.exe src\allotment_general.py
-----------ipo_allotment_manager----------
______fetch_allotment_holdings___ ZR1234
Other holdings found for ZR1234: []
No allotment found for user: 1
```

### 2. Main Daily Scheduler (`common_schedule_all.py`)

When starting the main 24/7 background scheduler:

```text
PS D:\CapitalFund1> .venv\Scripts\python.exe src\common_schedule_all.py
running now
-----------latest_ipo_entry---------
##############################################
Processing IPO Entries: 100%|████████████████████████████████████| 5/5 [00:10<00:00,  2.01s/ipo]
Email sent successfully with General.xlsx!
*************************************-----------daily_money_withdraw----------************************************
##############################################################################################################
Total Fund Required on: 8 is: 0
No withdrawal required.
*************************************-----------fund_trf_to_kite----------************************************
##############################################################################################################
No withdrawal required.
*************************************-----------smws_seller----------************************************
##############################################################################################################
sellnifty: 0
goldetfsell: 0
silveretfsell: 0
*************************************-----------smws_buyer----------************************************
##############################################################################################################
buynifty: 1
goldetfbuy: 0
silveretfbuy: 0
amount_per_security: 5400
-----------update_3pm----------
####################################
Finished
```

---

## Adding a New Account

1. Open `.env` and append a new user object to the `CAPITALFUND_USERS` JSON array.
2. Open `allotted_holdings.xlsx` and add a new sheet named with the new user's `uci` value.
3. Copy the header row from an existing sheet into the new sheet.
4. The system will automatically include this user in all future tasks.

---

## Mobile SMS Forwarding

Kotak sends OTP via SMS for fund transfers. To automate OTP reading:

1. On the client's Android phone, install **Automate** (from Play Store).
2. Create a flow: **Forward SMS containing keyword to Email**.
3. Set the SMS keyword to: `Kotak`
4. Set the destination Gmail to the `email_user` configured in `.env`.

The Python scripts check this Gmail inbox for the latest OTP email when a Kotak transaction requires SMS verification.
