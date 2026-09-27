# CapitalFund1 — Configuration & Setup Guide

This guide covers setting up, configuring, and verifying the CapitalFund1 system from scratch on a Windows workstation or server.

---

## 1. System Requirements

- **Operating System**: Windows 10/11 or Windows Server 2019+
- **Python**: Version 3.11 or higher
- **Browser**: Google Chrome installed (for Cloudscraper / Selenium) and Playwright Chromium
- **Network**: Stable, low-latency broadband connection (Indian IP required for NSE/BSE and Kotak NetBanking)

---

## 2. Step-by-Step Installation

### Step 2.1: Clone & Create Virtual Environment

Open PowerShell (Run as Administrator recommended for initial setup):

```powershell
# Navigate to project root
cd d:\CapitalFund1

# Create a dedicated virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate
```

### Step 2.2: Install Python Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.3: Install Playwright Browsers

> [!IMPORTANT]
> **Strict System Rule**: **We always use Playwright for Zerodha and Kotak NetBanking interactions, as it gives full operational control.**
> Do not attempt to replace browser automation with broker REST APIs (like Kite Connect API), which lack ASBA NetBanking capabilities, require recurring daily token authorizations, and introduce restrictive API rate limits.

Playwright drives headless browser automation for Zerodha Kite and Kotak NetBanking:

```powershell
playwright install chromium
```

---

## 3. Environment Variables Configuration (`.env`)

CapitalFund1 stores all secrets, credentials, and notification webhooks in a `.env` file located in the project root (`d:\CapitalFund1\.env`).

> [!CAUTION]
> Never commit `.env` or plaintext credentials to version control. The `.gitignore` file is configured to exclude `.env` and `credentials.json`.

Create or edit `.env`:

```env
# ==============================================================================
# Multi-Account Credentials Array (JSON)
# ==============================================================================
CAPITALFUND_USERS='[
  {
    "uci": "1",
    "name": "Primary Account Holder",
    "broker_client_id": "ZR1234",
    "password_broker": "BrokerPasswordHere",
    "topt_broker": "JBSWY3DPEHPK3PXP",
    "bank_user": "961633451",
    "bank_password": "BankPasswordHere",
    "email_user": "primary_account@gmail.com",
    "email_password": "xxxx xxxx xxxx xxxx",
    "PAN": "ABCDE1234F",
    "intraday": "0"
  },
  {
    "uci": "2",
    "name": "Secondary Account Holder",
    "broker_client_id": "ZR5678",
    "password_broker": "BrokerPasswordHere",
    "topt_broker": "KBSWY3DPEHPK3PXQ",
    "bank_user": "820484892",
    "bank_password": "BankPasswordHere",
    "email_user": "secondary_account@gmail.com",
    "email_password": "yyyy yyyy yyyy yyyy",
    "PAN": "FGHIJ5678K",
    "intraday": "1"
  }
]'

# ==============================================================================
# Telegram Real-Time Push Notifications
# ==============================================================================
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
TELEGRAM_CHAT_ID="987654321"

# ==============================================================================
# Email Alerts Engine (Gmail SMTP)
# ==============================================================================
ALERT_EMAIL_USER="system_alerts@gmail.com"
ALERT_EMAIL_PASS="zzzz zzzz zzzz zzzz"
```

---

## 4. Parameter Details

### User Object Schema (`CAPITALFUND_USERS`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `uci` | String / Int | Unique Client Identifier. Maps directly to sheet names in `allotted_holdings.xlsx` and `IPO-applied.xlsx`. |
| `name` | String | Account holder display name. |
| `broker_client_id` | String | Zerodha Kite 6-character user ID (e.g. `MFB802`). |
| `password_broker` | String | Zerodha Kite account password. |
| `topt_broker` | String | Base32 TOTP secret key generated during 2FA setup on Zerodha Kite. |
| `bank_user` | String | Kotak Mahindra NetBanking CRN or Nickname. |
| `bank_password` | String | Kotak Mahindra NetBanking password. |
| `email_user` | String | Gmail address configured to receive forwarded bank SMS OTPs. |
| `email_password` | String | 16-character Google App Password (not standard Gmail password). |
| `PAN` | String | 10-character Permanent Account Number for ASBA verification. |
| `intraday` | String (`"0"` or `"1"`) | Trading mode flag (`1` enables intraday product type). |

---

## 5. Third-Party Integrations Setup

### 5.1 Zerodha Kite 2FA (TOTP)
1. Log into [Kite Zerodha](https://kite.zerodha.com).
2. Go to **My Profile ➔ Password & Security ➔ Enable 2FA TOTP**.
3. Under the QR code, click **Can't scan? Copy key**.
4. Paste this alphanumeric base32 secret into the `topt_broker` field in `.env`.

### 5.2 Kotak SMS OTP Forwarding via Android Automate
Kotak NetBanking delivers login and transaction OTPs via SMS. To allow headless automation to retrieve OTPs:
1. Install **Automate** (or *SMS Forwarder*) on the Android smartphone receiving Kotak SMS.
2. Create a flow:
   - **Trigger**: Incoming SMS containing the word `Kotak` or `OTP`.
   - **Action**: Forward SMS content via email to the corresponding `email_user`.
3. Enable 2-Factor Authentication on the target Gmail account and generate a 16-digit **Google App Password**.
4. The system's IMAP client (`Base.py:get_netbanking_otp_sms`) connects over SSL, searches unread emails from the last 2 minutes, extracts the 6-digit OTP, and marks the email as read.

### 5.3 Telegram Push Notification Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a name and username, and copy the HTTP API token into `TELEGRAM_BOT_TOKEN`.
3. Start a conversation with your bot, then message [@userinfobot](https://t.me/userinfobot) to get your numerical user/chat ID.
4. Set `TELEGRAM_CHAT_ID` to this number.

---

## 6. Verification & Health Checks

Run the verification suite from the project root:

```powershell
.venv\Scripts\activate

# 1. Verify module imports and logging initialization
python -c "from common_schedule_all import *; print('✓ All modules imported successfully')"

# 2. Test Master.xlsx synchronization with credentials
python -c "import master_excel_manager; master_excel_manager.sync_master_with_credentials(); print('✓ Master.xlsx synchronized')"

# 3. Test Telegram Alert dispatch
python -c "from common_foundation import send_telegram_notification; send_telegram_notification('⚡ CapitalFund1 System Online'); print('✓ Telegram alert sent')"
```

---

## 7. Starting the System

### Option A: Interactive Mode (Development)
Open two PowerShell terminals:

```powershell
# Terminal 1: Launch Central 24/7 Automation Scheduler
.venv\Scripts\python.exe src\common_schedule_all.py

# Terminal 2: Launch Streamlit Control Hub Dashboard
.venv\Scripts\python.exe -m streamlit run dashboard.py
```

### Option B: Windows Task Scheduler / Daemon Autostart
To ensure 24/7 resilience across reboots, schedule `src/common_schedule_all.py` to run on system boot with highest privileges.
