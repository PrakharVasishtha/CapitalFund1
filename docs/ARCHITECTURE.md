# CapitalFund1 — System Architecture

## 1. System Overview

**CapitalFund1** is an autonomous, algorithmic trading and multi-account fund management platform engineered for the Indian equity and IPO markets. It orchestrates the entire operational lifecycle of IPO participation and tactical ETF management across multiple Zerodha Kite broker accounts integrated with Kotak Mahindra NetBanking.

The system operates autonomously 24/7, executing precision-timed daily tasks aligned with Indian market hours (08:00 to 15:30 IST) and post-market processing.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Streamlit Control Hub                           │
│                      (dashboard.py — Real-time Web UI)                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Reads / Monitors
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            Central 24/7 Scheduler                           │
│                   (src/common_schedule_all.py — Orchestrator)               │
└──────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────┘
       │              │              │              │              │
       ▼              ▼              ▼              ▼              ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│ IPO Research ││ Fund Routing ││ ETF Strategy ││ Application  ││ Listing Day  │
│  & Scraping  ││  & Banking   ││ (SMWS Engine)││ & Allotment  ││  Execution   │
│  (Chittor)   ││ (Kotak/Kite) ││ (GoogleSheet)││(Kotak/Console││(Pre-Open/Reg)│
└──────────────┘└──────────────┘└──────────────┘└──────────────┘└──────────────┘
       │              │              │              │              │
       └──────────────┴──────────────┼──────────────┴──────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │                 Data & State Persistence                │
        │  • General.xlsx (Research, Scoring, Listing Results)     │
        │  • allotted_holdings.xlsx (Multi-User Allotment State)  │
        │  • Master.xlsx (Multi-Account Profiles & Valuations)    │
        │  • IPO-applied.xlsx (Application History & Audit)       │
        │  • logs/ (Rotating error, capitalfund, audit logs)      │
        │  • Telemetry (Telegram Bot API & SMTP Email Alerts)     │
        └─────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 IPO Research & Intelligence Pipeline
- **Web Scraping**: Utilizes `cloudscraper` and `BeautifulSoup` to bypass Cloudflare and scrape Chittorgarh daily for Mainboard (`IPOMB`) and SME (`IPOSME`) IPOs.
- **Metric Extraction**:
  - Grey Market Premium (`ipo_ExtractGMP.py`)
  - Live institutional and retail subscription ratios (`ipo_ExtractSubscription.py`)
  - Analyst reviews and recommendations (`ipo_ExtractReview.py`)
  - Price-to-Earnings ratios (`ipo_pe.py`)
  - Pre-listing issue prices and post-listing opening prices (`ipo_listing_result.py`)
- **Scoring & Prioritization Engine**: Evaluates IPOs using a mathematical scoring model factoring in India VIX (`yfinance`), GMP percentage, and retail subscription multiples to assign apply priorities (`1`, `2`, `3`).

### 2.2 Fund Routing & Banking Engine
- **Dynamic Cash Calculation**: Assesses upcoming IPO capital requirements across Day 0 (today) and Day 1 (tomorrow) via `fund_manager.py`.
- **Automated Zerodha Withdrawal**: Triggers Playwright headless sessions to withdraw surplus capital from Zerodha Kite accounts to respective Kotak bank accounts.
- **Automated Bank-to-Broker Transfers**: Uses Playwright automation on Kotak NetBanking to transfer funds into Zerodha Kite.
- **SMS & IMAP OTP Bridge**: Connects via IMAP to Gmail accounts to intercept Kotak SMS OTPs forwarded from Android devices in real time.
- **Idle Cash Sweep**: Sweeps unused bank balances into Zerodha for ETF investments (`fund_transfer_for_smws.py`).

### 2.3 Systematic ETF Strategy Engine (SMWS)
- **Signal Ingestion**: Ingests automated trading signals from an external published Google Sheet CSV feed (`strategy_sheet.py`).
- **Target Assets**: Trades high-liquidity thematic ETFs:
  - `NIFTYIETF` (Nifty 50 Index ETF)
  - `TATAGOLD` (Gold ETF)
  - `TATSILV` (Silver ETF)
- **Order Execution**: Places slice-based market/limit buy and sell orders across all managed accounts via Zerodha Kite web automation.
- **Capital Priority Preemption**: Automatically liquidates ETF positions (`trader_priority_ipo_smws_sell.py`) when high-priority IPOs require immediate liquidity.

### 2.4 IPO Application & Allotment Management
- **Kotak NetBanking ASBA/UPI Applications**: Automates the multi-step ASBA IPO application flow using Playwright (`allotment_kotak_ipo_apply.py`). Dynamically selects between HNI (High Net-Worth Individual) and Retail bid lots based on available account funds.
- **Allotment Discovery**: Periodically logs into Zerodha Kite across all accounts to scan portfolio holdings. Discovers new scrips, discards default ETF symbols, and registers new allotments in `allotted_holdings.xlsx`.
- **Enrichment Pipeline**: Augments newly discovered allotments with listing date, lot size, issue price, and initializes listing day status codes.

### 2.5 Listing Day Execution Engine
The listing day strategy executes in two distinct chronological phases:

#### Phase A: Pre-Open Special Session (09:00 AM – 09:45 AM)
1. **09:00 AM**: Detects unexecuted allotments (`special_session_status == 5`) and immediately submits Lower Circuit (LC) sell orders to guarantee order queue priority.
2. **09:32 AM**: Queries Indicative Equilibrium Price (IEP) discovery feeds from NSE and BSE.
3. **Threshold Loss Check**:
   - Mainboard: If IEP shows an expected loss $> 11.9\%$, the LC sell order is canceled to prevent panic selling into pre-market anomalies.
   - SME: If IEP indicates listing at a discount ($< 0\%$), the order is evaluated or held.
   - If acceptable: Order remains live to execute at official open.

#### Phase B: Regular Market Session (10:01 AM Onwards)
For shares entering the regular trading session (`special_session_status != 2`):
1. **Market Depth Analysis**: Computes Buyer/Seller volume ratio:
   $$\text{Buyer Ratio \%} = \frac{\text{Total Buy Qty}}{\text{Total Buy Qty} + \text{Total Sell Qty}} \times 100$$
2. **Circuit Surveillance**:
   - If Buyer Ratio $\ge 60\%$: The stock is monitored for 30 minutes for Upper Circuit (UC) lock. If locked at UC, shares are held (`regular_session_status = 5`). If UC is not reached within 30 minutes, two stepped Good-Till-Triggered (GTT) sell orders are placed:
     - 50% shares @ $\text{LTP} + 2.0\%$
     - 50% shares @ $\text{LTP} + 5.0\%$
   - If Buyer Ratio $< 60\%$: High selling pressure triggers immediate defensive stepped GTT orders:
     - 50% shares @ $\text{LTP} + 0.5\%$
     - 50% shares @ $\text{LTP} + 1.0\%$

---

## 3. Technology Stack & Runtime Specifications

| Layer | Technologies |
| :--- | :--- |
| **Runtime & Language** | Python 3.11+, Windows PowerShell / Task Scheduler / Daemon |
| **Browser Automation** | Playwright (Chromium Async & Sync) — **Strict System Mandate for Zerodha & Kotak** |
| **Web Scraping** | Cloudscraper, BeautifulSoup4, Requests, curl_cffi, lxml, html5lib |
| **Storage Engine** | Dual-Tier: SQLite (`capitalfund.db` in WAL mode) + `openpyxl` atomic Excel sync |
| **Authentication & 2FA** | pyotp (RFC 6238 TOTP), IMAP4_SSL (Gmail automated OTP reader) |
| **Market Data** | yfinance (India VIX), NSE/BSE public HTTP endpoints |
| **Scheduling** | Python `schedule` engine with non-blocking daemon worker threads (`run_threaded`) |
| **User Interface** | Streamlit (Custom Glassmorphism Dark Theme, WebSocket auto-refresh) |
| **Telemetry & Alerts** | Telegram Bot API, Python `smtplib` / `EmailMessage`, RotatingFileHandler |

---

## 4. Multi-Account Architecture & Security

The system implements a credential isolation pattern:
- **No Plaintext Passwords in Git**: All sensitive account parameters (Zerodha client IDs, passwords, TOTP secret seeds, Kotak NetBanking credentials, Gmail app passwords, and PAN cards) reside in `.env` under `CAPITALFUND_USERS`.
- **Dynamic Multi-User Expansion**: The engine dynamically iterates over each profile in `CAPITALFUND_USERS`, generating unique TOTPs via `pyotp.TOTP(secret).now()`, performing isolated browser context sessions, and updating per-user sheets (`1`, `2`, ...) in `allotted_holdings.xlsx` and `IPO-applied.xlsx`.
- **Atomic File Operations**: All Excel modifications utilize `safe_load_workbook()` and `safe_save_workbook()` in `Base.py`, preventing workbook corruption via process-ID tagged temporary files (`.tmp_<PID>`) and atomic file replacement (`os.replace`).

---

## 5. Architectural Mandate: Playwright for Zerodha & Kotak

> [!IMPORTANT]
> **Core Architectural Rule**:
> **We always use Playwright for Zerodha and Kotak NetBanking interactions, as it gives full operational control.**
> Broker REST APIs (e.g., Kite Connect API) are deliberately avoided in favor of direct Playwright headless browser automation.

### Rationale & Design Drivers:
1. **Full Execution & DOM Control**: Playwright provides comprehensive control over browser cookies, local storage, DOM manipulation, and dynamic single-page application (SPA) states without being constrained by broker API restrictions, endpoint deprecations, or arbitrary rate limits.
2. **Autonomous Multi-Factor Authentication**: Automates the complete 2FA lifecycle natively — generating dynamic RFC 6238 TOTP tokens for Zerodha Kite and intercepting mobile SMS OTPs via IMAP for Kotak NetBanking — eliminating daily manual browser token logins.
3. **End-to-End ASBA NetBanking Support**: Kotak NetBanking does not provide public REST APIs for ASBA IPO applications or console fund sweeps. Playwright enables seamless navigation of the NetBanking portal, ASBA investor selection, bidding, and verification.
4. **Zero Vendor / Subscription Lock-in**: Eliminates dependencies on recurring API subscription fees, API developer keys, and third-party downtime.

---

## 6. Dual-Tier Storage Architecture & Concurrency

To ensure ultra-fast execution while preserving human-friendly Excel spreadsheets, CapitalFund1 implements a **Dual-Tier Storage Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                 Application Execution Layer                 │
│      (Scheduler, Allotment Detection, Listing Day, SMWS)     │
└──────────────┬───────────────────────────────▲──────────────┘
               │ Fast Writes (WAL)             │ Sub-millisecond Reads
               ▼                               │
┌─────────────────────────────────────────────────────────────┐
│             SQLite High-Performance Storage Engine          │
│                    (data/capitalfund.db)                    │
│   • master_users   • allotted_holdings   • ipo_research    │
│   • ipo_applied    • Write-Ahead Logging (WAL Mode)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Automatic Safe Sync
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Human-Readable Spreadsheets                 │
│  • Master.xlsx  • allotted_holdings.xlsx  • General.xlsx    │
│  • IPO-applied.xlsx (Atomic safe_save_workbook replacement) │
└─────────────────────────────────────────────────────────────┘
```

- **Concurrency-Safe SQLite Backend**: `capitalfund.db` operates in Write-Ahead Logging (`WAL`) mode with busy timeout handling, enabling continuous concurrent reads and writes without file locks or crashes.
- **Bi-directional Excel Synchronization**: SQLite state is safely mirrored to `Master.xlsx`, `allotted_holdings.xlsx`, `General.xlsx`, and `IPO-applied.xlsx` via atomic temporary file renaming (`.tmp_<PID>`). Operators can open and inspect Excel sheets at any time without triggering `PermissionError` in automated background jobs.
- **Non-Blocking Scheduler**: `src/common_schedule_all.py` runs all scheduled tasks via `run_threaded()` background daemon threads with re-entrancy locking. The main scheduler loop ticks uninterrupted every second, guaranteeing that precision market tasks (09:00 LC Sell, 09:32 IEP discovery, 10:01 Regular session) fire on the exact second.
