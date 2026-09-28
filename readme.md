# CapitalFund1 — Automated IPO Research, Allocation & Trading System

An enterprise automation engine for IPO research, multi-account fund routing, Kotak NetBanking ASBA applications, pre-open & regular session listing day trading, and allotment tracking across multiple Zerodha broker accounts integrated with Kotak Mahindra NetBanking.

---

## 📚 Complete Documentation Index

| Guide | Description |
| :--- | :--- |
| **[System Architecture](docs/ARCHITECTURE.md)** | Subsystems, technology stack, security boundaries, and high-level design. |
| **[Schedule & Workflows](docs/SCHEDULE_AND_WORKFLOWS.md)** | Chronological trading clock (08:00 – 15:30 IST) and detailed algorithmic workflows. |
| **[Configuration & Setup Guide](docs/CONFIGURATION_AND_SETUP.md)** | Installation, `.env` schema, Zerodha 2FA TOTP, and Android SMS OTP forwarding. |
| **[Data Dictionary & Schemas](docs/DATA_DICTIONARY_AND_SCHEMAS.md)** | Column definitions for `General.xlsx`, `allotted_holdings.xlsx`, `Master.xlsx`, and status codes. |
| **[Module Technical Reference](docs/MODULE_REFERENCE.md)** | Catalog of every source module in `src/`, key functions, and arguments. |
| **[Operations & Troubleshooting](docs/OPERATIONS_AND_TROUBLESHOOTING.md)** | Runbook, manual recovery triggers, OTP debugging, and Excel lock resolutions. |

> [!IMPORTANT]
> **Strict Automation Mandate: Playwright for Zerodha & Kotak**
> We always use **Playwright** for Zerodha Kite and Kotak NetBanking automation because it gives complete, end-to-end operational control over the DOM, dynamic 2FA TOTP/SMS OTP flows, NetBanking ASBA applications, order execution, and console fund routing without external REST API rate limits, daily token authorization overhead, or third-party subscription lock-in.

---

## ⚡ Core Capabilities

1. **Scrapes & Researches IPOs**: Automatically scrapes Chittorgarh daily for GMP, analyst consensus reviews, and live QIB/NII/Retail subscription metrics into `General.xlsx`.
2. **Dual-Tier Data Storage Engine**: Features a high-speed SQLite backend (`capitalfund.db` in WAL mode) for concurrent, non-blocking queries, paired with atomic Excel file synchronization (`safe_save_workbook()`), eliminating `PermissionError` file-lock conflicts.
3. **Non-Blocking Multi-Threaded Scheduler**: Runs time-critical tasks via `run_threaded()` background daemon workers so that heavy I/O never blocks the 1-second scheduler heartbeat.
4. **Automated ASBA Applications**: Submits ASBA IPO applications via Kotak NetBanking with dynamic HNI ($\ge \text{₹}200,001$) and Retail lot sizing.
5. **Dynamic Fund Routing**: Determines upcoming IPO cash needs across Day 0 and Day 1, withdrawing capital from Zerodha to Kotak, or sweeping idle bank balances into Zerodha.
6. **Allotment Detection**: Periodically inspects multi-account Zerodha portfolios, records newly allotted scrips in `allotted_holdings.xlsx`, and notifies via email and Telegram.
7. **Listing Day Execution**:
   - **09:00 AM Pre-Open**: Places Lower Circuit (LC) sell orders to secure queue priority.
   - **09:32 AM Discovery Check**: Compares Indicative Equilibrium Price (IEP) from NSE/BSE against loss thresholds (Mainboard $> 11.9\%$, SME $< 0\%$) to cancel or retain orders.
   - **10:01 AM Regular Session**: Analyzes market depth; holds locked Upper Circuit (UC) stocks, or deploys stepped Good-Till-Triggered (GTT) exit orders.
   - **10:05 AM Result Verification**: Verifies opening listing prices against issue prices and records results in `General.xlsx`.
8. **Tactical ETF Trading (SMWS)**: Executes systematic buy and sell orders for `NIFTYIETF`, `TATAGOLD`, and `TATSILV` based on external Google Sheet signals, with emergency preemption for IPO cash needs.
9. **Streamlit Control Hub**: Provides real-time portfolio valuations, live IPO analytics, SMWS monitors, and one-click execution triggers.

---

## 📁 Repository Structure

```text
CapitalFund1/
├── docs/                                   # Detailed system documentation
│   ├── ARCHITECTURE.md                     # System architecture & technical stack
│   ├── SCHEDULE_AND_WORKFLOWS.md           # Daily timeline & algorithmic workflows
│   ├── CONFIGURATION_AND_SETUP.md          # Setup, credentials, and SMS forwarding
│   ├── DATA_DICTIONARY_AND_SCHEMAS.md      # Excel schemas & lifecycle status codes
│   ├── MODULE_REFERENCE.md                 # Complete technical reference of src/
│   └── OPERATIONS_AND_TROUBLESHOOTING.md   # Daily runbook & failure resolutions
│
├── src/                                    # Application source code
│   ├── common_schedule_all.py              # Central 24/7 automation scheduler
│   ├── common_foundation.py                # Telemetry, email & Telegram alert engine
│   ├── logger_setup.py                     # Central structured logging (audit, rotating)
│   ├── Base.py                             # Atomic Excel handlers, TOTP, OTP & VIX
│   │
│   ├── regular_session_sell.py             # 10:01 AM: Depth ratio & stepped GTT orders
│   ├── special_sesion_zerodha_sell.py      # Pre-open LC sell orders & order cancellation
│   ├── ss_sale_order_on_lc_on_start_of_ss.py# 09:00 AM: Pre-open LC sell order initiator
│   ├── ss_Before_session_close_cancel_sale_or_not.py # 09:32 AM: IEP price monitor & cancel gate
│   ├── special_session_indicative_price_nse.py # NSE pre-open discovery scraper
│   ├── special_session_indicative_price_bse.py # BSE pre-open discovery scraper
│   │
│   ├── allotment_application_ipo.py        # Identifies closing IPOs & triggers applications
│   ├── allotment_kotak_ipo_apply.py        # Playwright: Kotak NetBanking ASBA submitter
│   ├── allotment_general.py                # Multi-account allotment detector
│   ├── allotment_fetch.py                  # Playwright: Scans Zerodha portfolio holdings
│   ├── allotment_update.py                 # Registers & enriches newly allotted holdings
│   │
│   ├── fund_manager.py                     # Calculates IPO funds & initiates Kite withdrawal
│   ├── fund_zerodha_withdraw.py            # Playwright: Zerodha Console fund withdrawal
│   ├── fund_bank_to_kite.py                # Playwright: Kotak to Zerodha fund transfer
│   ├── fund_transfer_for_smws.py           # Sweeps idle bank funds into Zerodha
│   ├── fund_kotak_get_balance.py           # Fetches Kotak bank balance via SMS OTP
│   │
│   ├── trader_smws.py                      # Systematic ETF buyer & seller
│   ├── trader_priority_ipo_smws_sell.py    # Liquidates ETFs when IPO cash is needed
│   ├── trader_zerodha_buy.py               # Playwright: Places ETF buy orders on Kite
│   ├── trader_zerodha_sell.py              # Playwright: Places ETF sell orders on Kite
│   ├── trader_zerodha_base.py              # Playwright: Margin balance & Kite session
│   ├── strategy_sheet.py                   # Shared Google Sheet signal reader
│   │
│   ├── ipo_scraper.py                      # Chittorgarh web scraper
│   ├── IpoDataExtractor.py                 # Structured IPO data parser
│   ├── ipo_ExtractGMP.py                   # Grey Market Premium scraper
│   ├── ipo_ExtractSubscription.py          # Subscription metrics scraper
│   ├── ipo_ExtractReview.py                # Analyst consensus reviews
│   ├── ipo_pe.py                           # P/E ratio calculations
│   ├── ipo_listing_result.py               # 10:05 AM: Chittorgarh listing performance
│   │
│   ├── master_excel_manager.py             # Synchronizes Master.xlsx with credentials
│   └── ipo_applied_manager.py              # Logs applications to IPO-applied.xlsx
│
├── dashboard.py                            # Streamlit Control Hub web application
├── General.xlsx                            # Primary IPO research database
├── allotted_holdings.xlsx                  # Multi-account allotment tracker
├── Master.xlsx                             # User profiles & portfolio valuations
├── IPO-applied.xlsx                        # Historical application logs
├── requirements.txt                        # Python dependencies
└── .env                                    # Environment secrets (gitignored)
```

---

## ⏱️ Daily Operational Schedule

| Time | Scheduled Task | Description |
| :--- | :--- | :--- |
| **08:00** | `launch_streamlit_dashboard` | Launches Streamlit Control Hub on port 8501 (if not running). |
| **08:30** | `ipo_entry` | Scrapes newly announced IPO listings into `General.xlsx`. |
| **08:35** | `update_dynamic_data` | Refreshes subscription metrics, GMP, and analyst reviews. |
| **08:40** | `allotment_general` | Inspects Zerodha holdings for new IPO allotments across accounts. |
| **09:00** | `ss_start_lc_sell` | Places Lower Circuit (LC) sell orders for newly allotted shares. |
| **09:05** | `money_withdraw` | Computes Day 0/1 IPO fund requirements & withdraws Zerodha ➔ Kotak. |
| **09:10** | `bank_to_kite` | Sweeps idle Kotak Bank funds to Zerodha Kite for SMWS trading. |
| **09:15** | `smws_seller` | Sells SMWS ETFs (`NIFTYIETF`, `TATAGOLD`, `TATSILV`) per signals. |
| **09:20** | `priority_ipo_sell_smws` | Liquidates SMWS ETFs if immediate IPO capital is needed. |
| **09:25** | `smws_buyer` | Buys SMWS ETFs per strategy signals using available margin slices. |
| **09:32** | `cancel_sale_order_if_loss` | Queries NSE/BSE indicative prices; cancels LC order if loss threshold exceeded. |
| **10:01** | `regular_session_ipo_sell` | Regular session depth analysis (holds locked UC, or places stepped GTTs). |
| **10:05** | `listing_result` | Verifies opening listing prices vs issue price on Chittorgarh; updates Col D. |
| **12:05** | `update_dynamic_data` | Mid-day subscription and GMP refresh. |
| **14:47** | `update_dynamic_data` | Pre-close subscription refresh. |
| **14:50** | `ipo_application` | Submits Kotak ASBA applications for IPOs closing today. |

---

## 📊 Status Code Lifecycle (`allotted_holdings.xlsx`)

### `special_session_status` (Column 8)
- `0` : Not started
- `1` : Special session Lower Circuit (LC) sell order placed (09:00 AM)
- `2` : Order executed / Sold in pre-open special session
- `3` : Order canceled due to loss threshold; transferred to regular session
- `5` : Newly detected allotment (pending initial order placement)

### `regular_session_status` (Column 11)
- `0` : Not started / Sold in pre-open
- `1` : Eligible for regular session selling (pre-open order was canceled)
- `2` : Sold / Stepped GTT exit orders placed on Kite
- `3` : Not sold during regular market hours
- `5` : Held locked at Upper Circuit (UC)

---

## 🚀 Quick Start

### 1. Environment Setup

```powershell
cd d:\CapitalFund1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Credentials

Create a `.env` file in the project root:

```env
CAPITALFUND_USERS='[
  {
    "uci": "1",
    "name": "Primary User",
    "broker_client_id": "ZR1234",
    "password_broker": "Password",
    "topt_broker": "BASE32SECRET",
    "bank_user": "CRN_NUMBER",
    "bank_password": "BankPassword",
    "email_user": "user@gmail.com",
    "email_password": "app_password",
    "PAN": "ABCDE1234F",
    "intraday": "0"
  }
]'

TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
TELEGRAM_CHAT_ID="987654321"
ALERT_EMAIL_USER="alerts@gmail.com"
ALERT_EMAIL_PASS="gmail_app_password"
```

### 3. Run System

```powershell
# Start Central 24/7 Automation Scheduler
.venv\Scripts\python.exe src\common_schedule_all.py

# Launch Streamlit Control Hub (in a separate terminal)
.venv\Scripts\python.exe -m streamlit run dashboard.py
```