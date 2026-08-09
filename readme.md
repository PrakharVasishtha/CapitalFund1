# CapitalFund1 — Automated IPO Research, Allocation & Trading System

An enterprise automation engine for managing IPO research, fund routing, UPI applications, pre-open/regular session listing day trading, and allotment tracking across multiple Zerodha broker accounts integrated with Kotak NetBanking.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Quick Setup](#quick-setup)
- [Automated Selling Strategies](#automated-selling-strategies)
- [Daily Trading Schedule](#daily-trading-schedule)
- [Database & Excel Reference](#database--excel-reference)
- [Status Code Definitions](#status-code-definitions)
- [Streamlit Control Hub](#streamlit-control-hub)
- [SMS & Telegram Alerts Setup](#sms--telegram-alerts-setup)

---

## Overview

CapitalFund1 automates the complete lifecycle of IPO investments:

1. **Scrapes & Research**: Scrapes Chittorgarh daily for GMP, analyst reviews, and live subscription metrics into `General.xlsx`.
2. **UPI Applications**: Automates Kotak NetBanking UPI applications for shortlisted IPOs.
3. **Fund Routing**: Dynamically withdraws funds from Zerodha to Kotak for applications, or sweeps idle bank cash into ETF strategies (SMWS).
4. **Allotment Detection**: Scans multi-account Zerodha portfolios and records new allotments in `allotted_holdings.xlsx` and `IPO-applied.xlsx`.
5. **Listing Day Execution**: Executes pre-open special session and regular session selling strategies (GTT & Lower Circuit orders).
6. **Real-time Notifications**: Sends push alerts via Telegram for applications, allotments, fund routing, and listing orders.

---

## System Architecture

```text
CapitalFund1/
├── src/
│   ├── common_schedule_all.py              # Main 24/7 automation scheduler
│   ├── common_foundation.py                # Logging, email, & Telegram notification engine
│   ├── common_master_functions.py          # Data entry, 3 PM close updates
│   │
│   ├── regular_session_sell.py             # Regular session selling strategy (Buyer/Seller ratio & GTT)
│   ├── special_sesion_zerodha_sell.py      # Pre-open special session LC sell orders
│   ├── ss_sale_order_on_lc_on_start_of_ss.py# Triggers pre-open LC sell orders on listing day
│   ├── ss_Before_session_close_cancel_sale_or_not.py # Pre-open price monitoring & order cancellation
│   │
│   ├── allotment_application_ipo.py        # Evaluates & ranks IPOs closing today
│   ├── allotment_kotak_ipo_apply.py        # Playwright: Kotak UPI application submitter
│   ├── allotment_general.py                # Multi-account allotment detector
│   ├── allotment_fetch.py                  # Playwright: Scans Zerodha portfolio holdings
│   ├── allotment_update.py                 # Enriches allotted holdings with GMP & subscription
│   │
│   ├── fund_manager.py                     # Calculates IPO funds & triggers Zerodha withdrawal
│   ├── fund_zerodha_withdraw.py            # Playwright: Zerodha to Kotak bank withdrawal
│   ├── fund_bank_to_kite.py                # Playwright: Kotak bank to Zerodha fund transfer
│   ├── fund_transfer_for_smws.py           # Sweeps idle bank funds into Zerodha
│   ├── fund_kotak_get_balance.py           # Fetches Kotak bank balance via SMS OTP
│   │
│   ├── trader_smws.py                      # SMWS ETF buyer & seller (NIFTYIETF, TATAGOLD, TATSILV)
│   ├── trader_priority_ipo_smws_sell.py    # Sells SMWS ETFs when IPO funds are required
│   ├── trader_zerodha_buy.py               # Playwright: Places ETF buy orders on Zerodha
│   ├── trader_zerodha_sell.py              # Playwright: Places ETF sell orders on Zerodha
│   ├── trader_zerodha_base.py              # Playwright: Fetches Zerodha margin balance & updates Master
│   │
│   ├── master_excel_manager.py             # Central manager for Master.xlsx synchronization
│   ├── ipo_applied_manager.py              # Central manager for IPO-applied.xlsx logging
│   └── Base.py                             # Shared helpers: credentials, formulas, & VIX
│
├── dashboard.py                            # Streamlit Control Hub web application
├── General.xlsx                            # Primary IPO research database
├── allotted_holdings.xlsx                  # Allotment portfolio tracker (per-user sheets)
├── Master.xlsx                             # Master account profiles & valuations
├── IPO-applied.xlsx                        # History of submitted applications (sheets 1, 2)
├── requirements.txt                        # Python dependencies
└── .env                                    # Environment secrets (gitignored)
```

---

## Quick Setup

### 1. Install Dependencies

```powershell
cd d:\CapitalFund1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Secrets (`.env`)

Create a `.env` file in the project root:

```env
# Multi-Account Credentials Array
CAPITALFUND_USERS='[
  {
    "uci": "1",
    "name": "Account Holder 1",
    "broker_client_id": "ZR1234",
    "password_broker": "zerodha_password",
    "topt_broker": "TOTP_BASE32_SECRET",
    "bank_user": "kotak_user_id",
    "bank_password": "kotak_password",
    "email_user": "user1@gmail.com",
    "email_password": "gmail_app_password",
    "PAN": "ABCDE1234F",
    "intraday": "0"
  }
]'

# Telegram Push Notifications
TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
TELEGRAM_CHAT_ID="987654321"

# Email Alerts
ALERT_EMAIL_USER="user@gmail.com"
ALERT_EMAIL_PASS="gmail_app_password"
```

---

## Automated Selling Strategies

### 1. Pre-Open Special Session (09:00 AM – 09:45 AM)

- **Mainboard (MB)**:
  - If pre-open indicative price indicates positive listing (>0%), **DO NOT SELL** during pre-open.
  - If indicative price shows discount/loss (Loss > 11.9% or Indicative Price > -12%), place a Lower Circuit (LC) sell order immediately.
- **SME Listings**:
  - If depth & indicative price at BSE/NSE indicate negative listing, place a Lower Circuit (LC) sell order immediately (*sell at any cost*).

### 2. Regular Trading Session (10:01 AM Onwards)

Executed for all allotted shares **not sold in the special pre-open session**:

| Market Condition | 30-Min Upper Circuit (UC) Check | Action Taken |
| :--- | :--- | :--- |
| **Buyer/Seller Ratio > 60%** (High Demand) | **UC Hit within 30 mins** | **DO NOT SELL** (Hold shares locked at UC). |
| **Buyer/Seller Ratio > 60%** (High Demand) | **No UC after 30 mins** | Place **GTT Order 1** for 50% shares @ `LTP + 2%`<br>Place **GTT Order 2** for 50% shares @ `LTP + 5%`. |
| **Buyer/Seller Ratio < 60%** (Selling Pressure) | *Immediate Placement* | Place **GTT Order 1** for 50% shares @ `LTP + 0.5%`<br>Place **GTT Order 2** for 50% shares @ `LTP + 1.0%`. |

$$\text{Buyer Ratio \%} = \frac{\text{Total Buy Quantity}}{\text{Total Buy Quantity} + \text{Total Sell Quantity}} \times 100$$

---

## Daily Trading Schedule

| Time | Function | Description |
| :--- | :--- | :--- |
| **Startup** | `run_now()` | Syncs `Master.xlsx` and runs setup tasks on script start |
| **08:30** | `ipo_entry()` | Scrapes new IPO listings from Chittorgarh into `General.xlsx` |
| **08:35** | `update_dynamic_data()` | Refreshes subscription, GMP, and reviews in `General.xlsx` |
| **08:40** | `allotment_general()` | Scans Zerodha portfolio holdings for new IPO allotments |
| **09:00** | `ss_start_lc_sell()` | Places LC sell orders for newly allotted IPO shares |
| **09:05** | `money_withdraw()` | Calculates required IPO funds & withdraws Zerodha ➔ Kotak |
| **09:10** | `bank_to_kite()` | Sweeps idle Kotak bank funds into Zerodha Kite for SMWS |
| **09:15** | `smws_seller()` | Sells SMWS ETFs (`NIFTYIETF`, `TATAGOLD`, `TATSILV`) per signals |
| **09:20** | `priority_ipo_sell_smws()`| Sells SMWS ETFs when IPO funds are required |
| **09:25** | `smws_buyer()` | Buys SMWS ETFs per Google Sheet strategy signals |
| **09:32** | `cancel_sale_order_if_loss()`| Cancels pre-open LC sell orders if loss threshold exceeded |
| **10:01** | `regular_session_ipo_sell()`| Executes regular session selling strategy (Buyer Ratio & GTT) |
| **12:05** | `update_dynamic_data()` | Mid-day subscription and GMP refresh |
| **14:52** | `update_dynamic_data()` | Pre-close subscription refresh |
| **14:55** | `ipo_application()` | Submits Kotak UPI applications for closing IPOs & logs to `IPO-applied.xlsx` |

---

## Database & Excel Reference

### 1. `General.xlsx` (IPO Research Database)
- **Sheets**: `IPOMB` (Mainboard) & `IPOSME` (SME).
- **Columns**: `Company Name` (Col 2), `ClosingDate (40)`, `Apply Priority (42)`, `Total Score`, `GMP`, `Retail Sub`.

### 2. `allotted_holdings.xlsx` (Portfolio Holdings Tracker)
- **Sheets**: Per-user sheets named by UCI (e.g. `"1"`, `"2"`).
- **Columns**: `security_name` (Col 1), `lot_size` (Col 2), `issue_price` (Col 3), `shares_allocated` (Col 4), `exchange` (Col 6), `special_session_status` (Col 8), `regular_session_status` (Col 11).

### 3. `Master.xlsx` (Master User Accounts & Valuation)
- **Sheet**: `Users`.
- **Columns**: `uci` (Col 1), `first_name` (Col 2), `account_email` (Col 6), `intraday` (Col 7), `zerodha_access_token` (Col 8), `current_value` (Col 9).

### 4. `IPO-applied.xlsx` (Submitted Application Log)
- **Sheets**: Per-user sheets named `1`, `2`.
- **Columns**: `IPO-Name` (Col 1), `Shares Applied` (Col 2), `Issue price` (Col 3), `Total Application amount` (Col 4).

---

## Status Code Definitions

### `special_session_status` (Column 8 of `allotted_holdings.xlsx`)
- `0`: Not started
- `1`: Special session LC sell order placed
- `2`: Sold in special pre-open session
- `3`: Order canceled / Not sold in special session
- `5`: Newly detected allotment (pending enrichment)

### `regular_session_status` (Column 11 of `allotted_holdings.xlsx`)
- `0`: Not started
- `1`: Eligible for regular session strategy
- `2`: Sold / GTT orders placed in regular session
- `3`: Not sold in regular session
- `5`: Held at Upper Circuit (UC)

---

## Streamlit Control Hub

Launch the web dashboard:

```powershell
.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Features:
- **Executive Summary**: Live account valuations (`Master.xlsx`), allotted securities, and IPO schedule filters.
- **Balances & Capital Manager**: Multi-account profile cards and `Master.xlsx` database table.
- **IPO Analytics**: Mainboard, SME, and High-Gain (>20% GMP) tabs.
- **SMWS Strategy Monitor**: Live buy/sell ETF signals with color-coded pills.
- **System Health & Telegram Diagnostics**: Real-time console output viewer and Telegram test push alert trigger.

---

## SMS & Telegram Alerts Setup

### 1. Telegram Push Notifications
1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram to obtain `TELEGRAM_BOT_TOKEN`.
2. Get your Chat ID from [@userinfobot](https://t.me/userinfobot) to obtain `TELEGRAM_CHAT_ID`.
3. Add both to `.env`. Real-time push alerts will be sent for applications, allotments, fund routing, and sell orders.

### 2. Kotak SMS OTP Forwarding
To automate Kotak bank login OTPs:
1. Install **Automate** (or SMS Forwarder) on the client's Android phone.
2. Create a rule: Forward SMS containing `Kotak` to the account's `email_user`.
3. The Playwright scripts automatically extract OTPs from Gmail inbox.