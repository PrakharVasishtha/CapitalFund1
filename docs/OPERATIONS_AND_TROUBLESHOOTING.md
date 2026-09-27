# CapitalFund1 — Operations & Troubleshooting Runbook

This guide covers operational procedures, routine health monitoring, manual recovery workflows, and troubleshooting common failure modes.

---

## 1. Daily Operations Runbook

### 1.1 Morning Routine (08:00 – 08:30 AM IST)
1. **Verify Scheduler & Dashboard**:
   - Ensure the scheduler process (`python src/common_schedule_all.py`) is running.
   - Open the Streamlit Control Hub in a browser (`http://localhost:8501`).
2. **Review Telegram Online Alert**:
   - Verify that the morning Telegram heartbeat / startup alert was received.
3. **Inspect Allotments & Listing Schedule**:
   - On the Streamlit Dashboard, check the **Allotted Securities** panel.
   - Confirm if any IPO shares are scheduled to list today.

### 1.2 Listing Hour Monitoring (09:00 – 10:15 AM IST)
1. **09:00 AM (Pre-Open LC Sell)**:
   - Check Telegram for execution confirmation of pre-open Lower Circuit sell orders.
   - Check `allotted_holdings.xlsx` to confirm `special_session_status` transitioned from `5` to `1`.
2. **09:32 AM (Indicative Price Discovery & Cancellation Check)**:
   - Review whether pre-open orders were canceled (`status = 3`) or allowed to execute (`status = 2`).
3. **10:01 AM (Regular Session GTT Execution)**:
   - If shares entered regular trading, confirm that market depth was evaluated and stepped GTT orders were placed (`regular_session_status = 2`).

### 1.3 Afternoon Application Window (14:50 – 15:05 PM IST)
1. **Check IPO Applications**:
   - Confirm automated ASBA application submissions for IPOs closing today.
   - Verify application numbers logged in `IPO-applied.xlsx`.

---

## 2. Manual Triggers & Overrides

### 2.1 Triggering Scheduled Tasks Manually
Tasks can be triggered on demand via the Streamlit Dashboard or PowerShell:

```powershell
.venv\Scripts\activate

# Scrape Chittorgarh IPOs and update database
python -c "import common_master_functions; common_master_functions.latest_ipo_entry()"

# Refresh GMP, reviews, and subscriptions
python -c "import common_master_functions; common_master_functions.dynamic_data_update()"

# Check Zerodha holdings for new allotments
python -c "import allotment_general; allotment_general.ipo_allotment_manager()"

# Run fund requirement check and trigger withdrawal
python -c "import fund_manager; fund_manager.daily_money_withdraw()"

# Execute SMWS ETF buy cycle
python -c "import trader_smws; trader_smws.smws_buyer()"

# Force update listing results (10:05 AM task)
python -c "import ipo_listing_result; ipo_listing_result.update_listing_results()"
```

### 2.2 Manual Priority Overrides in `General.xlsx`
If you wish to force an IPO to be applied (or skipped):
1. Open `General.xlsx`.
2. Locate the target company in `IPOMB` or `IPOSME`.
3. Modify Column 42 (`Apply Priority`):
   - Set to `3` for Top Priority
   - Set to `2` for High Priority
   - Set to `1` for Normal Apply
   - Set to `0` to Avoid / Skip
4. Save and close `General.xlsx`.

---

## 3. Troubleshooting Common Failure Modes

### 3.1 Playwright Headless vs Headful & Browser Freezes
- **Symptom**: Browser automation hangs indefinitely or fails to find login elements on Kotak or Zerodha.
- **Root Cause**: Bank UI changes, CAPTCHA challenge, or headless detection.
- **Resolution**:
  1. Temporarily toggle `headless=False` in the respective script (e.g. `allotment_kotak_ipo_apply.py` or `trader_zerodha_base.py`) to observe the browser window.
  2. Clear cached browser profiles in `%USERPROFILE%\AppData\Local\ms-playwright`.
  3. Ensure Chrome/Chromium is updated: `playwright install chromium`.

### 3.2 Bank SMS OTP Interception Failure
- **Symptom**: `get_netbanking_otp_sms` times out after 7 attempts with `Attempt X: Searching for OTP... None`.
- **Root Causes**:
  1. **Phone Offline**: Android device running Automate/SMS Forwarder is disconnected from Wi-Fi/cellular data.
  2. **Clock Drift**: The time on the machine running CapitalFund1 differs from Google's server time by $> 2$ minutes, causing `time_diff > 2` check to reject valid emails.
  3. **Gmail App Password Revoked**: Google revoked the 16-character App Password.
- **Resolution**:
  1. Synchronize the Windows system clock: **Settings ➔ Time & Language ➔ Sync now**.
  2. Send a test SMS to the forwarding phone and verify it arrives in the `email_user` Gmail inbox within 10 seconds.
  3. Verify Gmail IMAP access is enabled in Gmail settings.

### 3.3 Zerodha 2FA / TOTP Desynchronization
- **Symptom**: Zerodha Kite login repeatedly fails with `Invalid TOTP` or `Two-factor authentication failed`.
- **Root Cause**: Windows system clock is skewed by more than 30 seconds, causing `pyotp.TOTP(secret).now()` to generate invalid codes.
- **Resolution**:
  1. Run PowerShell as Administrator:
     ```powershell
     w32tm /resync
     ```
  2. Verify TOTP code generated matches Google Authenticator:
     ```powershell
     python -c "import pyotp; print(pyotp.TOTP('YOUR_SECRET_HERE').now())"
     ```

### 3.4 Excel Permission Denied (`.tmp_` Files)
- **Symptom**: `PermissionError: [Errno 13] Permission denied: 'General.xlsx'` or leftover `.tmp_XXXX` files.
- **Root Cause**: An interactive Excel application has the workbook open exclusively, or an antivirus process is scanning the file during `os.replace`.
- **Resolution**:
  1. Close all open instances of Microsoft Excel before scheduled market execution times.
  2. Clean up orphaned temporary files:
     ```powershell
     Remove-Item General.xlsx.tmp_* -Force -ErrorAction SilentlyContinue
     ```
  3. The built-in `safe_save_workbook()` automatically retries up to 5 times.

### 3.5 Google Sheet Strategy CSV Delay
- **Symptom**: `trader_smws.py` or `fund_manager.py` outputs `sheet not loading` or `Invalid signal value in sheet`.
- **Root Cause**: Google Sheets published CSV web links occasionally cache stale data or return empty strings.
- **Resolution**:
  - The shared `strategy_sheet.py` module includes automatic timestamp busting (`&t=...`) and 10 retries with 2-second delays.
  - Test connectivity in browser: Open the published Google Sheet link in an incognito window to verify values in Row 24, Column 5.

### 3.6 Cloudflare Scraping Challenge
- **Symptom**: `ipo_scraper.py` fails with HTTP 403 Forbidden.
- **Root Cause**: Chittorgarh updated anti-bot protections.
- **Resolution**:
  1. Ensure `cloudscraper` and `curl_cffi` are on the latest versions:
     ```powershell
     pip install --upgrade cloudscraper curl_cffi
     ```

---

## 4. System Maintenance & Cleanup

Run monthly maintenance to keep disk and log sizes lean:

```powershell
# Archive or remove logs older than 60 days
Get-ChildItem -Path "d:\CapitalFund1\logs" -Filter "*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-60) } | Remove-Item -Force

# Verify git repository status
git status
```
