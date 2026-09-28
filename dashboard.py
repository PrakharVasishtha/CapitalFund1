import os
import sys
import re
import time
import glob

import datetime
import json
import pandas as pd
import openpyxl
import streamlit as st

# Ensure project root & src are in path
_curr_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_curr_dir).lower() == "src":
    BASE_DIR = os.path.dirname(_curr_dir)
else:
    BASE_DIR = _curr_dir
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import html
import job_manager

# Import local utilities
try:
    from Base import load_credentials, parse_float
except ImportError:
    def load_credentials():
        raw = os.environ.get("CAPITALFUND_USERS")
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                pass
        return [
            {"uci": "1", "name": "Prakhar", "broker_client_id": "MFB802", "bank_user": "961633451", "intraday": "0", "PAN": "AQOPV6354N"},
            {"uci": "2", "name": "Sonam", "broker_client_id": "PUT824", "bank_user": "820484892", "intraday": "1", "PAN": "JSNPS4632G"}
        ]
    def parse_float(val):
        try:
            val_str = str(val).replace('%','').replace('₹','').replace(',','').replace('Cr','').strip()
            return float(val_str)
        except Exception:
            return 0.0

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Glassmorphism Styling System
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CapitalFund1 — Enterprise Automation & Trading Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Dark Theme System Palette */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #080d1a 90%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Premium Glassmorphic Cards */
    .glass-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(12px);
        margin-bottom: 18px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.5);
        box-shadow: 0 14px 35px -5px rgba(56, 189, 248, 0.15);
    }

    /* Metric Labels & Values */
    .kpi-title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #ffffff;
    }
    .kpi-footer {
        font-size: 0.82rem;
        color: #38bdf8;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Color Classes */
    .text-emerald { color: #34d399 !important; }
    .text-cyan { color: #38bdf8 !important; }
    .text-indigo { color: #818cf8 !important; }
    .text-amber { color: #fbbf24 !important; }
    .text-rose { color: #f87171 !important; }

    /* Custom Badges */
    .pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .pill-green { background: rgba(52, 211, 153, 0.16); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.35); }
    .pill-amber { background: rgba(251, 191, 36, 0.16); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.35); }
    .pill-blue { background: rgba(56, 189, 248, 0.16); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); }
    .pill-purple { background: rgba(168, 85, 247, 0.16); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); }
    .pill-red { background: rgba(244, 63, 94, 0.16); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.35); }

    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.3; transform: scale(0.85); }
    }
    .pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        margin-right: 6px;
        animation: pulse-dot 1.5s infinite ease-in-out;
        vertical-align: middle;
    }

    /* Custom Console Container */
    .console-box {
        background-color: #020617;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.84rem;
        color: #cbd5e1;
        max-height: 440px;
        overflow-y: auto;
        line-height: 1.6;
    }

    /* Section Divider */
    .section-head {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 10px;
        margin-bottom: 22px;
        color: #f8fafc;
        font-weight: 700;
        font-size: 1.25rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Right Side Panel Styling */
    .side-panel-box {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.88) 0%, rgba(8, 13, 26, 0.96) 100%);
        border: 1px solid rgba(56, 189, 248, 0.28);
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
        margin-bottom: 16px;
    }
    .side-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loaders with Caching (Short TTL for responsive auto-refresh)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10)
def load_ipo_database():
    excel_path = os.path.join(BASE_DIR, "General.xlsx")
    if not os.path.exists(excel_path):
        return pd.DataFrame(), pd.DataFrame()
    for attempt in range(5):
        try:
            df_sme = pd.read_excel(excel_path, sheet_name="IPOSME")
            df_mb = pd.read_excel(excel_path, sheet_name="IPOMB")
            return df_sme, df_mb
        except Exception as e:
            if attempt == 4:
                st.error(f"Error loading General.xlsx: {e}")
                return pd.DataFrame(), pd.DataFrame()
            time.sleep(0.3)
    return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=10)
def load_allotted_holdings():
    path = os.path.join(BASE_DIR, "allotted_holdings.xlsx")
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        xls = pd.ExcelFile(path)
        all_sheets = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df['uci'] = str(sheet)
            all_sheets.append(df)
        if all_sheets:
            combined = pd.concat(all_sheets, ignore_index=True)
            combined = combined.dropna(subset=['security_name'])
            return combined
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading allotted_holdings.xlsx: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def load_master_database():
    try:
        from master_excel_manager import get_master_excel_path
        path = get_master_excel_path()
        if os.path.exists(path):
            df = pd.read_excel(path, sheet_name="Users")
            return df
    except Exception as e:
        print(f"load_master_database error: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=15)
def fetch_smws_signals():
    """
    Fetch SMWS signals from the Google Sheet strategy tab.

    Strategy for resolving "Loading..." values caused by un-recalculated
    GOOGLEFINANCE / cross-sheet IMPORTRANGE formulas:
      1. Attempt to read the CSV directly (fast path).
      2. If any signal value contains "Loading...", trigger the Playwright
         sheet warmer to force Google's server-side recalculation.
      3. Wait ~5 s, then retry the CSV read (up to 5 total attempts).
      4. Cache successful signals to SQLite smws_signals table.
      5. If all attempts still show "Loading...", fall back to the most
         recent cached values from SQLite (never show raw "Loading...").
    """
    import time as _time

    url_csv = (
        "https://docs.google.com/spreadsheets/d/e/"
        "2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-"
        "BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?gid=614695683&single=true&output=csv"
    )

    def _read_signals(df: "pd.DataFrame") -> dict:
        """Extract the six signal cells from a DataFrame row."""
        return {
            "buy_nifty": str(df.iloc[23, 4]).strip() if len(df) > 23 else "Loading...",
            "buy_gold": str(df.iloc[26, 4]).strip() if len(df) > 26 else "Loading...",
            "buy_silver": str(df.iloc[29, 4]).strip() if len(df) > 29 else "Loading...",
            "sell_nifty": str(df.iloc[24, 4]).strip() if len(df) > 24 else "Loading...",
            "sell_gold": str(df.iloc[27, 4]).strip() if len(df) > 27 else "Loading...",
            "sell_silver": str(df.iloc[30, 4]).strip() if len(df) > 30 else "Loading...",
        }

    def _has_loading(signals: dict) -> bool:
        return any("loading" in str(v).lower() for v in signals.values())

    def _save_to_sqlite(signals: dict) -> None:
        """Persist clean signals to SQLite for fallback use."""
        try:
            import sys as _sys
            if SRC_DIR not in _sys.path:
                _sys.path.insert(0, SRC_DIR)
            from database import get_connection, init_db
            init_db()
            conn = get_connection()
            conn.execute(
                """INSERT INTO smws_signals
                   (buy_nifty, buy_gold, buy_silver, sell_nifty, sell_gold, sell_silver, source)
                   VALUES (?, ?, ?, ?, ?, ?, 'GOOGLE_SHEET')""",
                (
                    signals["buy_nifty"], signals["buy_gold"], signals["buy_silver"],
                    signals["sell_nifty"], signals["sell_gold"], signals["sell_silver"],
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _load_from_sqlite() -> dict:
        """Return the most recently cached SMWS signals from SQLite, or empty dict."""
        try:
            import sys as _sys
            if SRC_DIR not in _sys.path:
                _sys.path.insert(0, SRC_DIR)
            from database import get_connection, init_db
            init_db()
            conn = get_connection()
            row = conn.execute(
                "SELECT buy_nifty, buy_gold, buy_silver, sell_nifty, sell_gold, sell_silver, updated_at "
                "FROM smws_signals ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
            conn.close()
            if row:
                return {
                    "buy_nifty": row["buy_nifty"] or "0",
                    "buy_gold": row["buy_gold"] or "0",
                    "buy_silver": row["buy_silver"] or "0",
                    "sell_nifty": row["sell_nifty"] or "0",
                    "sell_gold": row["sell_gold"] or "0",
                    "sell_silver": row["sell_silver"] or "0",
                    "_from_cache": True,
                    "_cache_time": str(row["updated_at"]),
                }
        except Exception:
            pass
        return {}

    warmed = False
    signals = {}
    raw_df = None

    for attempt in range(1, 6):
        try:
            raw_df = pd.read_csv(url_csv, timeout=20)
            signals = _read_signals(raw_df)

            if not _has_loading(signals):
                # ✅ Clean signals — cache and return
                _save_to_sqlite(signals)
                signals["raw_df"] = raw_df
                return signals

            # Signals have "Loading..." — warm sheet on first detection
            if not warmed:
                try:
                    import sys as _sys
                    if SRC_DIR not in _sys.path:
                        _sys.path.insert(0, SRC_DIR)
                    from smws_sheet_warmer import recalculate_smws_sheet
                    recalculate_smws_sheet(force=True)
                except Exception:
                    pass
                warmed = True

            if attempt < 5:
                _time.sleep(5)

        except Exception as e:
            if attempt == 5:
                return {"error": str(e)}
            _time.sleep(3)

    # All attempts exhausted — try SQLite cache
    cached = _load_from_sqlite()
    if cached:
        cached["raw_df"] = raw_df
        return cached

    # Absolute last resort — return whatever we have (might still show Loading)
    if signals:
        signals["raw_df"] = raw_df
        return signals

    return {"error": "Unable to load SMWS signals after 5 attempts"}

def read_logs(log_type="error"):
    if log_type == "error":
        path = os.path.join(BASE_DIR, "logs", "error.log")
    else:
        path = os.path.join(BASE_DIR, "system.txt")
    
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                return lines[-250:] # Return last 250 lines
        except Exception as e:
            return [f"Error reading file: {e}"]
    return ["Log file does not exist yet."]

def clean_company_name(name):
    s = str(name).replace('&amp;', '&').strip()
    s = re.sub(r'\s*(?:Price|GMP|Date|Pric|Pr|GM)\b.*$', '', s, flags=re.IGNORECASE).strip()
    return s

def clean_ipo_dataframe(df, category_name="Mainboard"):
    if df.empty:
        return pd.DataFrame()
    
    today_day = datetime.date.today().day
    clean = pd.DataFrame()
    clean['Company Name'] = df['Company Name'].apply(clean_company_name)
    clean['Category'] = category_name
    clean['Issue Price (₹)'] = df['Issue price'].apply(parse_float) if 'Issue price' in df.columns else 0.0
    clean['GMP (₹)'] = df['GMP'].apply(parse_float) if 'GMP' in df.columns else 0.0
    
    clean['Listing Gain %'] = clean.apply(
        lambda r: round((r['GMP (₹)'] / r['Issue Price (₹)'] * 100), 2) if r['Issue Price (₹)'] > 0 else 0.0,
        axis=1
    )
    
    # Total Score (>23 / >13.1)
    score_col = 'Total >23' if 'Total >23' in df.columns else ('Total >13.1' if 'Total >13.1' in df.columns else None)
    if not score_col:
        score_cols = [c for c in df.columns if 'total' in str(c).lower()]
        score_col = score_cols[0] if score_cols else None
    clean['Total Score'] = df[score_col].apply(parse_float) if score_col and score_col in df.columns else 0.0

    # Apply Recommendation (Appy_or_not / Apply_priority)
    apply_col = 'Appy_or_not' if 'Appy_or_not' in df.columns else None
    prio_col = 'Apply_priority' if 'Apply_priority' in df.columns else None
    
    def get_apply_str(row):
        val = row.get(prio_col) if prio_col else (row.get(apply_col) if apply_col else 0)
        p = parse_float(val)
        if p == 3: return '🟢 Apply (P3)'
        elif p == 2: return '🟢 Apply (P2)'
        elif p == 1: return '🟡 Apply (P1)'
        elif p > 0: return '🟢 Apply'
        else: return '🔴 Avoid / 0'
        
    clean['Apply Recommendation'] = df.apply(get_apply_str, axis=1)

    # Retail Subscription (RII <1.34 / RII)
    rii_col = 'RII <1.34' if 'RII <1.34' in df.columns else ('RII' if 'RII' in df.columns else None)
    clean['Retail Sub (x)'] = df[rii_col].apply(parse_float) if rii_col and rii_col in df.columns else 0.0

    # Closing Day & Status
    close_cols = [c for c in df.columns if 'closingdate' in str(c).lower().replace(' ', '')]
    def parse_close_day(val):
        try:
            return int(float(val))
        except Exception:
            return 0
    clean['Close Day'] = df[close_cols[0]].apply(parse_close_day) if close_cols else 0
    clean['Close Date'] = clean['Close Day'].apply(lambda d: f"Day {d}" if d > 0 else "N/A")
    clean['Is Closing Today'] = clean['Close Day'] == today_day
    
    clean = clean[clean['Company Name'].str.strip() != "nan"]
    clean = clean[clean['Company Name'].str.strip() != ""]
    return clean.sort_values(by="Listing Gain %", ascending=False)

@st.cache_data(ttl=10)
def load_userwise_applied_data():
    """
    Loads userwise applied IPO records, amounts, lots/shares, and live execution failure logs
    from IPO-applied.xlsx, user text log files (1.txt, 2.txt), and SQLite WAL ipo_applied.
    """
    users = load_credentials()
    uci_to_name = {str(u.get('uci')): u.get('name', f"User {u.get('uci')}") for u in users}

    # 1. Parse user log text files for live execution status & failure reasons
    user_logs = {}
    for txt_file in glob.glob(os.path.join(BASE_DIR, "[0-9]*.txt")):
        base_name = os.path.basename(txt_file)
        clean_uci = base_name.replace(".txt", "").strip()
        if clean_uci not in user_logs:
            user_logs[clean_uci] = {}
        try:
            with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split(" at MM-DD HH:MM :")
                    if len(parts) == 2:
                        prefix, dt = parts[0], parts[1]
                        if " : " in prefix:
                            res, ipo = prefix.split(" : ", 1)
                            clean_name = clean_company_name(ipo).lower()
                            user_logs[clean_uci][clean_name] = {
                                "result": res.strip(),
                                "timestamp": dt.strip(),
                                "raw_ipo": ipo.strip()
                            }
        except Exception:
            pass

    records = []
    seen_keys = set()

    # 2. Ingest from IPO-applied.xlsx
    excel_path = os.path.join(BASE_DIR, "IPO-applied.xlsx")
    if os.path.exists(excel_path):
        try:
            xls = pd.ExcelFile(excel_path)
            for sheet_name in xls.sheet_names:
                clean_uci = str(sheet_name).replace("user", "").replace("User", "").strip()
                df_sheet = pd.read_excel(xls, sheet_name=sheet_name)
                for _, row in df_sheet.iterrows():
                    raw_name = str(row.get("IPO-Name", "")).strip()
                    if not raw_name or raw_name.lower() == "nan":
                        continue

                    shares = int(parse_float(str(row.get("Shares Applied", 1))))
                    price = abs(parse_float(str(row.get("Issue price", 0.0))))
                    amount = abs(parse_float(str(row.get("Total Application amount", 0.0))))
                    if amount == 0.0 and shares > 0 and price > 0:
                        amount = round(shares * price, 2)

                    status = str(row.get("Status", "APPLIED")).strip()
                    failure_reason = str(row.get("Failure Reason", "")).strip()

                    # Reconcile with user log files
                    clean_key = clean_company_name(raw_name).lower()
                    log_match = user_logs.get(clean_uci, {}).get(clean_key)
                    if not log_match:
                        for logged_name, logged_data in user_logs.get(clean_uci, {}).items():
                            if logged_name in clean_key or clean_key in logged_name:
                                log_match = logged_data
                                break

                    applied_dt = "N/A"
                    if log_match:
                        applied_dt = log_match.get("timestamp", "N/A")
                        res_val = log_match.get("result", "")
                        if res_val and any(err_word in res_val.lower() for err_word in ["error", "not applied", "otp", "failed", "fail"]):
                            status = "FAILED"
                            failure_reason = res_val
                        elif res_val in ["None", "applied in retail", "applied in SNI", "OK"]:
                            status = "APPLIED"
                            failure_reason = ""

                    user_name = uci_to_name.get(clean_uci, f"User {clean_uci}")
                    category = "SME" if "sme" in raw_name.lower() else "Mainboard"
                    lot_display = f"{shares:,} Shares" if shares > 1 else "1 Lot"

                    records.append({
                        "UCI": clean_uci,
                        "User Name": user_name,
                        "Account": f"{user_name} (UCI {clean_uci})",
                        "IPO Name": clean_company_name(raw_name),
                        "Raw IPO Name": raw_name,
                        "Category": category,
                        "Shares Applied": shares,
                        "Lots / Quantity": lot_display,
                        "Issue Price (₹)": price,
                        "Total Amount (₹)": amount,
                        "Status": status,
                        "Failure Reason": failure_reason if failure_reason and failure_reason != "nan" else "None (Successful)",
                        "Applied Date": applied_dt
                    })
                    seen_keys.add((clean_uci, clean_company_name(raw_name).lower()))
        except Exception as e:
            print(f"Error loading IPO-applied.xlsx: {e}")

    # 3. Ingest from SQLite ipo_applied
    try:
        from database import get_applied_ipos
        db_rows = get_applied_ipos()
        for r in db_rows:
            clean_uci = str(r.get("uci", "")).strip()
            raw_name = str(r.get("ipo_name", "")).strip()
            clean_name = clean_company_name(raw_name)
            dedup_key = (clean_uci, clean_name.lower())
            if dedup_key not in seen_keys:
                user_name = uci_to_name.get(clean_uci, f"User {clean_uci}")
                shares = int(r.get("shares_applied", 1))
                price = abs(float(r.get("issue_price", 0.0)))
                amt = abs(float(r.get("total_amount", 0.0)))
                stat = r.get("status", "APPLIED")
                fail = r.get("failure_reason") or "None (Successful)"
                dt = r.get("applied_date", "N/A")

                # Reconcile with live user logs
                clean_key = clean_name.lower()
                log_match = user_logs.get(clean_uci, {}).get(clean_key)
                if not log_match:
                    for logged_name, logged_data in user_logs.get(clean_uci, {}).items():
                        if logged_name in clean_key or clean_key in logged_name:
                            log_match = logged_data
                            break
                if log_match:
                    dt = log_match.get("timestamp", dt)
                    res_val = log_match.get("result", "")
                    if res_val and any(err_word in res_val.lower() for err_word in ["error", "not applied", "otp", "failed", "fail"]):
                        stat = "FAILED"
                        fail = res_val
                    elif res_val in ["None", "applied in retail", "applied in SNI", "OK"]:
                        stat = "APPLIED"
                        fail = "None (Successful)"

                records.append({
                    "UCI": clean_uci,
                    "User Name": user_name,
                    "Account": f"{user_name} (UCI {clean_uci})",
                    "IPO Name": clean_name,
                    "Raw IPO Name": raw_name,
                    "Category": "SME" if "sme" in raw_name.lower() else "Mainboard",
                    "Shares Applied": shares,
                    "Lots / Quantity": f"{shares:,} Shares",
                    "Issue Price (₹)": price,
                    "Total Amount (₹)": amt,
                    "Status": stat,
                    "Failure Reason": fail,
                    "Applied Date": dt
                })
                seen_keys.add(dedup_key)
    except Exception as e:
        print(f"Error reading SQLite ipo_applied: {e}")

    df_applied = pd.DataFrame(records)
    applied_lookup = {}
    for r in records:
        key = (str(r["UCI"]), r["IPO Name"].lower())
        applied_lookup[key] = r

    return df_applied, applied_lookup

# Check internet connectivity
def check_internet():
    import urllib.request
    try:
        urllib.request.urlopen("https://www.google.com", timeout=2)
        return True
    except Exception:
        return False

# -----------------------------------------------------------------------------
# Sidebar Configuration & Navigation
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="margin: 0; font-weight: 800; color: #38bdf8;">CapitalFund1</h2>
    <p style="margin: 2px 0; font-size: 0.8rem; color: #94a3b8;">Trading & Allotment Engine v2.0</p>
</div>
""", unsafe_allow_html=True)

nav = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Executive Dashboard",
        "⚡ Job Scheduler & Live Controls",
        "💰 Balances & Account Manager",
        "🧮 IPO Funding & Margin Calculator",
        "🚀 IPO Analytics & Predictions",
        "📈 Live SMWS Strategy Monitor",
        "📦 Allotted Holdings Tracker",
        "📜 System Health & Activity Logs"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Live Operations & Display")
show_right_panel = st.sidebar.checkbox(
    "📌 Show Jobs Log Panel",
    value=True,
    help="Display the real-time jobs log table and execution controls in the right-hand panel."
)

auto_refresh_choice = st.sidebar.selectbox(
    "🔄 Auto-Refresh Rate",
    ["Every 5s", "Every 10s", "Every 30s", "Every 60s", "Paused"],
    index=1,
    help="Interval for automatically refreshing dashboard metrics and data."
)

refresh_sec_map = {
    "Every 5s": 5,
    "Every 10s": 10,
    "Every 30s": 30,
    "Every 60s": 60,
    "Paused": None
}
auto_refresh_sec = refresh_sec_map.get(auto_refresh_choice, 10)

if auto_refresh_sec:
    st.sidebar.markdown(f'<span class="pill pill-green"><span class="pulse-dot"></span>Auto-Refresh: {auto_refresh_choice}</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="pill pill-purple">⚪ Auto-Refresh Paused</span>', unsafe_allow_html=True)

if st.sidebar.button("🔄 Refresh All Data Now", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
internet_ok = check_internet()
if internet_ok:
    st.sidebar.markdown('<span class="pill pill-green">🌐 Internet Connected</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="pill pill-amber">⚠️ Internet Offline</span>', unsafe_allow_html=True)

st.sidebar.caption(f"Server Time: {datetime.datetime.now().strftime('%H:%M:%S IST')}")

# -----------------------------------------------------------------------------
# Main Banner Header
# -----------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #0f172a 100%); padding: 24px 30px; border-radius: 16px; margin-bottom: 24px; border: 1px solid rgba(99, 102, 241, 0.35); box-shadow: 0 12px 36px rgba(0,0,0,0.4);">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 style="margin: 0; font-size: 1.95rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
                CapitalFund1 Control Hub
            </h1>
            <p style="margin: 6px 0 0 0; color: #cbd5e1; font-size: 0.95rem;">
                Unified Automation Dashboard for Zerodha Kite, Kotak NetBanking & IPO Research
            </p>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 10px;">
            <span class="pill pill-blue">Multi-Account Engine</span>
            <span class="pill pill-green">Playwright Ready</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Global Data Fetching Helper
# -----------------------------------------------------------------------------
def load_all_dashboard_data():
    """Load fresh instances of all core datasets."""
    users = load_credentials()
    df_sme_raw, df_mb_raw = load_ipo_database()
    df_sme_clean = clean_ipo_dataframe(df_sme_raw, "SME")
    df_mb_clean = clean_ipo_dataframe(df_mb_raw, "Mainboard")
    df_all_ipos = pd.concat([df_mb_clean, df_sme_clean], ignore_index=True)
    df_allotments = load_allotted_holdings()
    df_master = load_master_database()

    df_sme_last10 = clean_ipo_dataframe(df_sme_raw.tail(10), "SME") if not df_sme_raw.empty else pd.DataFrame()
    df_mb_last10 = clean_ipo_dataframe(df_mb_raw.tail(10), "Mainboard") if not df_mb_raw.empty else pd.DataFrame()
    df_recent_active = pd.concat([df_mb_last10, df_sme_last10], ignore_index=True) if (not df_sme_last10.empty or not df_mb_last10.empty) else df_all_ipos

    df_applied, applied_lookup = load_userwise_applied_data()

    return users, df_sme_raw, df_mb_raw, df_sme_clean, df_mb_clean, df_all_ipos, df_allotments, df_master, df_recent_active, df_applied, applied_lookup

# Initial load for global context
users, df_sme_raw, df_mb_raw, df_sme_clean, df_mb_clean, df_all_ipos, df_allotments, df_master, df_recent_active, df_applied, applied_lookup = load_all_dashboard_data()

# -----------------------------------------------------------------------------
# Real-Time Job Scheduler & On-Demand Controller Components
# -----------------------------------------------------------------------------

def render_live_job_status_and_output(show_output_box: bool = True):
    """
    Renders timestamped current running jobs, next scheduled job, and live output stream.
    Decorated with @st.fragment(run_every=3) for automatic live updates every 3 seconds.
    """
    @st.fragment(run_every=3)
    def _fragment_view():
        col1, col2 = st.columns(2)

        # (1) Timestamped current jobs running
        running_jobs = job_manager.get_currently_running_jobs()
        state = job_manager.get_job_state()
        last_comp = state.get("last_completed")

        with col1:
            if running_jobs:
                for rj in running_jobs:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 5px solid #10b981;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span class="pill pill-green"><span class="pulse-dot"></span>RUNNING NOW</span>
                            <span style="font-size:0.8rem; color:#94a3b8;">Triggered by: <b>{html.escape(str(rj.get('triggered_by', 'Scheduler')))}</b></span>
                        </div>
                        <h3 style="margin:4px 0; color:#ffffff;">{html.escape(str(rj.get('name', rj.get('job_key', 'Job'))))}</h3>
                        <div style="font-size:0.88rem; color:#cbd5e1; margin-top:8px;">
                            <p style="margin:2px 0;">⏰ <b>Started At:</b> <code style="color:#38bdf8;">{rj.get('started_at', 'N/A')}</code></p>
                            <p style="margin:2px 0;">⏳ <b>Elapsed Time:</b> <span class="pill pill-amber">{rj.get('elapsed_str', '0s')}</span></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                last_comp_html = ""
                if last_comp:
                    status_badge = '<span class="pill pill-green">SUCCESS</span>' if last_comp.get("status") == "SUCCESS" else '<span class="pill pill-red">FAILED</span>'
                    last_comp_html = f"""
                    <div style="margin-top:10px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.08); font-size:0.82rem; color:#94a3b8;">
                        <b>Last Completed:</b> {html.escape(str(last_comp.get('name', 'N/A')))} &nbsp;|&nbsp; {status_badge}<br>
                        Finished: <code>{last_comp.get('finished_at', 'N/A')}</code> ({last_comp.get('duration_seconds', 0)}s)
                    </div>
                    """
                st.markdown(f"""
                <div class="glass-card" style="border-left: 5px solid #64748b;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pill pill-purple">⚪ IDLE</span>
                        <span style="font-size:0.8rem; color:#64748b;">No active tasks</span>
                    </div>
                    <h3 style="margin:6px 0 2px 0; color:#94a3b8;">Scheduler Idle</h3>
                    <p style="margin:0; font-size:0.86rem; color:#64748b;">Waiting for next scheduled tick or on-demand command.</p>
                    {last_comp_html}
                </div>
                """, unsafe_allow_html=True)

        # (1b) Next job to run
        next_job = job_manager.get_next_scheduled_job()
        with col2:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #38bdf8;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span class="pill pill-blue">⏰ NEXT SCHEDULED JOB</span>
                    <span class="pill pill-amber">⏳ {next_job['countdown_str']}</span>
                </div>
                <h3 style="margin:4px 0; color:#ffffff;">{next_job['icon']} {html.escape(str(next_job['name']))}</h3>
                <div style="font-size:0.88rem; color:#cbd5e1; margin-top:8px;">
                    <p style="margin:2px 0;">📅 <b>Scheduled Time:</b> <code style="color:#38bdf8;">{next_job['scheduled_time']}</code></p>
                    <p style="margin:2px 0; color:#94a3b8;">ℹ️ {html.escape(str(next_job['description']))}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # (2) Output of the current job running
        if show_output_box:
            hdr_col1, hdr_col2 = st.columns([3, 1])
            with hdr_col1:
                st.markdown("<b>💻 Current / Recent Job Output Stream</b> &nbsp;<span style='font-size:0.75rem; color:#94a3b8;'>(Live Auto-Refresh every 3s)</span>", unsafe_allow_html=True)
            with hdr_col2:
                if st.button("🗑️ Clear Output", key="btn_clear_job_out", help="Clear current job log file"):
                    try:
                        open(job_manager.CURRENT_JOB_LOG, "w").close()
                    except Exception:
                        pass
                    st.rerun()

            current_output = job_manager.get_current_job_output(max_lines=150)
            st.markdown(f"<div class='console-box' style='max-height: 280px;'>{html.escape(current_output)}</div>", unsafe_allow_html=True)

    _fragment_view()


def render_jobs_log_side_panel():
    """
    Renders the dedicated live Jobs Log Table, running task monitor, and output/audit viewer
    in the right-hand panel of the dashboard.
    Decorated with @st.fragment(run_every=3) for automatic real-time updates every 3 seconds.
    """
    @st.fragment(run_every=3)
    def _fragment_side_panel():
        st.markdown("""
        <div class="side-panel-header">
            <div>
                <span style="color:#38bdf8; font-weight:800; font-size:1.05rem;">⚡ Jobs Operations Panel</span>
                <div style="font-size:0.75rem; color:#94a3b8;">Real-time task telemetry & control</div>
            </div>
            <span class="pill pill-green"><span class="pulse-dot"></span>LIVE (3s)</span>
        </div>
        """, unsafe_allow_html=True)

        # 1. Active Running Job or Next Scheduled Job Card
        running_jobs = job_manager.get_currently_running_jobs()
        if running_jobs:
            for rj in running_jobs:
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid #10b981; padding: 14px; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pill pill-green"><span class="pulse-dot"></span>RUNNING NOW</span>
                        <span class="pill pill-amber">⏳ {rj.get('elapsed_str', '0s')}</span>
                    </div>
                    <div style="font-weight:700; color:#ffffff; margin:6px 0 2px 0; font-size:0.95rem;">{html.escape(str(rj.get('name', rj.get('job_key', 'Job'))))}</div>
                    <div style="font-size:0.78rem; color:#94a3b8;">
                        Started: <code style="color:#38bdf8;">{rj.get('started_at', 'N/A')}</code> &bull; By: <b>{html.escape(str(rj.get('triggered_by', 'Scheduler')))}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            next_job = job_manager.get_next_scheduled_job()
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid #38bdf8; padding: 14px; margin-bottom: 12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="pill pill-blue">⚪ IDLE</span>
                    <span class="pill pill-amber">⏳ {next_job['countdown_str']}</span>
                </div>
                <div style="font-weight:700; color:#ffffff; margin:6px 0 2px 0; font-size:0.95rem;">Next: {next_job['icon']} {html.escape(str(next_job['name']))}</div>
                <div style="font-size:0.78rem; color:#94a3b8;">
                    Scheduled: <code style="color:#38bdf8;">{next_job['scheduled_time']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 2. Jobs Execution Log Table
        st.markdown("<div style='font-size:0.9rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;'>📋 Jobs Execution Log Table</div>", unsafe_allow_html=True)
        df_history = job_manager.get_job_history_df(limit=25)
        st.dataframe(df_history, use_container_width=True, hide_index=True, height=220)

        # 3. Live Console Stream & System Logs Tabs
        panel_tabs = st.tabs(["💻 Job Output", "📜 System Logs"])
        with panel_tabs[0]:
            h_c1, h_c2 = st.columns([2.5, 1])
            with h_c1:
                st.caption("Logs from `current_job.log`")
            with h_c2:
                if st.button("🗑️ Clear", key="btn_side_clear_out", use_container_width=True):
                    try:
                        open(job_manager.CURRENT_JOB_LOG, "w").close()
                    except Exception:
                        pass
                    st.rerun()
            out_txt = job_manager.get_current_job_output(max_lines=80)
            st.markdown(f"<div class='console-box' style='max-height: 200px; font-size:0.78rem;'>{html.escape(out_txt)}</div>", unsafe_allow_html=True)

        with panel_tabs[1]:
            st.caption("Logs from `capitalfund.log`")
            sys_log_txt = job_manager.get_recent_system_logs(max_lines=40)
            st.markdown(f"<div class='console-box' style='max-height: 200px; font-size:0.78rem;'>{html.escape(sys_log_txt)}</div>", unsafe_allow_html=True)

        # 4. Quick Action Triggers & Universal Job Dispatcher
        st.markdown("<div style='font-size:0.9rem; font-weight:700; color:#cbd5e1; margin:12px 0 6px 0;'>⚡ Universal Job Dispatcher</div>", unsafe_allow_html=True)
        job_options = list(job_manager.JOB_REGISTRY.keys())
        selected_side_job = st.selectbox(
            "Select Workflow to Trigger",
            options=job_options,
            format_func=lambda k: f"{job_manager.JOB_REGISTRY[k]['icon']} {job_manager.JOB_REGISTRY[k]['name']}",
            key="side_select_job",
            label_visibility="collapsed"
        )
        if st.button("▶️ Execute Workflow Now", key="side_btn_exec_selected", use_container_width=True, help="Trigger selected job immediately in background"):
            job_name = job_manager.JOB_REGISTRY[selected_side_job]["name"]
            if job_manager.run_job(selected_side_job, triggered_by="Side Panel (Dropdown)"):
                st.toast(f"▶️ Triggered '{job_name}'!")
                st.rerun()
            else:
                st.warning("Job is already running. Please wait.")

        st.markdown("<div style='font-size:0.82rem; font-weight:600; color:#94a3b8; margin:8px 0 4px 0;'>Quick Shortcuts:</div>", unsafe_allow_html=True)
        q1, q2 = st.columns(2)
        with q1:
            if st.button("🗄️ Sync DB", key="side_btn_sync_db", use_container_width=True, help="Synchronize SQLite WAL database & Excel sheets"):
                if job_manager.run_job("sync_database", triggered_by="Side Panel (Quick)"):
                    st.toast("🗄️ Started Dual-Tier SQLite Sync!")
                    st.rerun()
                else:
                    st.warning("Job already running")
            if st.button("🚀 Scrape IPOs", key="side_btn_scrape_ipo", use_container_width=True, help="Scrape latest IPOs from Chittorgarh"):
                if job_manager.run_job("ipo_entry", triggered_by="Side Panel (Quick)"):
                    st.toast("🚀 Started IPO Scraper!")
                    st.rerun()
                else:
                    st.warning("Job already running")
        with q2:
            if st.button("📊 Dynamic Data", key="side_btn_dyn_data", use_container_width=True, help="Refresh subscription & GMP"):
                if job_manager.run_job("update_dynamic_data", triggered_by="Side Panel (Quick)"):
                    st.toast("📊 Started Dynamic Data Update!")
                    st.rerun()
                else:
                    st.warning("Job already running")
            if st.button("📋 Allotments", key="side_btn_allotments", use_container_width=True, help="Check Zerodha holdings for allotments"):
                if job_manager.run_job("allotment_general", triggered_by="Side Panel (Quick)"):
                    st.toast("📋 Checking Allotments!")
                    st.rerun()
                else:
                    st.warning("Job already running")

    _fragment_side_panel()


def render_on_demand_buttons():
    """
    Renders categorized buttons to perform all 19 system functions,
    grouped according to the 6 operational flow stages.
    """
    st.markdown("<div class='section-head'>⚡ On-Demand Flow Execution Controller</div>", unsafe_allow_html=True)
    st.caption("Trigger any of the 19 automated functions on-demand. Buttons are organized sequentially by operational flow stages (08:00 – 15:30 IST).")

    flow_tab1, flow_tab2, flow_tab3, flow_tab4, flow_tab5, flow_tab6 = st.tabs([
        "🌅 1. Pre-Market (08:00)",
        "💰 2. Funds Sweep (09:05)",
        "📈 3. SMWS Trading (09:15)",
        "⚡ 4. Pre-Open (09:00)",
        "🎯 5. Market Execution (10:00)",
        "🗄️ 6. System & Sync"
    ])

    # ── Flow 1: Pre-Market Intelligence (08:00 - 08:59) ──
    with flow_tab1:
        st.markdown("""
        <div style="background:rgba(56, 189, 248, 0.08); border-left:4px solid #38bdf8; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.84rem; color:#cbd5e1;">
            <b>Flow Stage 1: Pre-Market Intelligence & Research (08:00 – 08:59 IST)</b><br>
            Scrapes new issues, updates live GMP/subscriptions, scans portfolios for new allotments, and ensures dashboard uptime.
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("🌐 Verify / Launch Hub", use_container_width=True, key="btn_flow_launch_streamlit_dashboard", help="Verify port 8501 and launch Streamlit Control Hub if offline"):
                if job_manager.run_job("launch_streamlit_dashboard", triggered_by="Flow 1 (On-Demand)"):
                    st.toast("🌐 Started 'Verify / Launch Dashboard'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 08:00 IST • Health Check")
        with c2:
            if st.button("🚀 Scrape Latest IPOs", use_container_width=True, key="btn_flow_ipo_entry", help="Scrapes latest IPOs from Chittorgarh into General.xlsx"):
                if job_manager.run_job("ipo_entry", triggered_by="Flow 1 (On-Demand)"):
                    st.toast("🚀 Started 'Scrape Latest IPOs'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 08:30 IST • Chittorgarh Scrape")
        with c3:
            if st.button("📊 Dynamic Data & GMP", use_container_width=True, key="btn_flow_update_dynamic_data", help="Refreshes GMP, subscriptions & formula scores in General.xlsx"):
                if job_manager.run_job("update_dynamic_data", triggered_by="Flow 1 (On-Demand)"):
                    st.toast("📊 Started 'Update Dynamic Data & GMP'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 08:35, 12:05, 14:47 IST")
        with c4:
            if st.button("📋 Scan Allotments", use_container_width=True, key="btn_flow_allotment_general", help="Check Zerodha Kite holdings for new allotments & sync allotted_holdings.xlsx"):
                if job_manager.run_job("allotment_general", triggered_by="Flow 1 (On-Demand)"):
                    st.toast("📋 Started 'Scan Holdings for Allotments'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 08:40 IST • Kite Holdings")

    # ── Flow 2: Funds Management & Sweeping (09:05 - 09:10) ──
    with flow_tab2:
        st.markdown("""
        <div style="background:rgba(16, 185, 129, 0.08); border-left:4px solid #10b981; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.84rem; color:#cbd5e1;">
            <b>Flow Stage 2: Funds Management & Capital Sweeping (09:05 – 09:10 IST)</b><br>
            Inspects Kotak NetBanking balances, calculates IPO capital reserve requirements, and moves idle capital between Kite and Bank.
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏦 Refresh Kotak Balances", use_container_width=True, key="btn_flow_refresh_kotak_balance", help="Inspect live available Kotak NetBanking balances across all user accounts"):
                if job_manager.run_job("refresh_kotak_balance", triggered_by="Flow 2 (On-Demand)"):
                    st.toast("🏦 Started 'Refresh Kotak Balances'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⚡ On-Demand • Kotak Playwright")
        with c2:
            if st.button("💸 Calc Reserves & Withdraw", use_container_width=True, key="btn_flow_money_withdraw", help="Calculates IPO fund reserve requirements and withdraws surplus Kite funds to Kotak bank"):
                if job_manager.run_job("money_withdraw", triggered_by="Flow 2 (On-Demand)"):
                    st.toast("💸 Started 'Calculate Reserves & Withdraw'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:05 IST • Kite to Kotak")
        with c3:
            if st.button("🔄 Sweep Idle Cash to Kite", use_container_width=True, key="btn_flow_bank_to_kite", help="Transfers excess idle Kotak bank funds into Zerodha Kite for SMWS systematic trading"):
                if job_manager.run_job("bank_to_kite", triggered_by="Flow 2 (On-Demand)"):
                    st.toast("🔄 Started 'Sweep Idle Cash to Kite'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:10 IST • Kotak to Kite")

    # ── Flow 3: SMWS Systematic ETF Trading (09:15 - 09:30) ──
    with flow_tab3:
        st.markdown("""
        <div style="background:rgba(245, 158, 11, 0.08); border-left:4px solid #f59e0b; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.84rem; color:#cbd5e1;">
            <b>Flow Stage 3: SMWS Systematic ETF Trading (09:15 – 09:30 IST)</b><br>
            Executes systematic ETF trades (NIFTYIETF, TATAGOLD, TATSILV) according to the live strategy sheet, and triggers priority liquidations if IPO funds are required.
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📉 Execute SMWS ETF Sell", use_container_width=True, key="btn_flow_smws_seller", help="Sells SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on signal"):
                if job_manager.run_job("smws_seller", triggered_by="Flow 3 (On-Demand)"):
                    st.toast("📉 Started 'SMWS ETF Sell'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:15 IST • Systematic Sell")
        with c2:
            if st.button("⚠️ Priority IPO Sell for Funds", use_container_width=True, key="btn_flow_priority_ipo_sell_smws", help="Liquidates SMWS ETFs when IPO application funds are required today"):
                if job_manager.run_job("priority_ipo_sell_smws", triggered_by="Flow 3 (On-Demand)"):
                    st.toast("⚠️ Started 'Priority IPO Sell for Funds'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:20 IST • Capital Liquidation")
        with c3:
            if st.button("📈 Execute SMWS ETF Buy", use_container_width=True, key="btn_flow_smws_buyer", help="Buys SMWS ETFs based on strategy sheet buy signal"):
                if job_manager.run_job("smws_buyer", triggered_by="Flow 3 (On-Demand)"):
                    st.toast("📈 Started 'SMWS ETF Buy'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:25 IST • Systematic Buy")

    # ── Flow 4: Pre-Open Listing Day Trading (09:00 - 09:45) ──
    with flow_tab4:
        st.markdown("""
        <div style="background:rgba(239, 68, 68, 0.08); border-left:4px solid #ef4444; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.84rem; color:#cbd5e1;">
            <b>Flow Stage 4: Pre-Open Listing Day Operations (09:00 – 09:45 IST)</b><br>
            Places pre-open LC sell orders on Zerodha Kite for listing shares, monitors live indicative equilibrium prices (IEP), and cancels LC if discount limit is exceeded.
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⚡ Place Pre-Open LC Sell", use_container_width=True, key="btn_flow_ss_start_lc_sell", help="Places Lower Circuit sell order on Zerodha Kite for newly allotted shares"):
                if job_manager.run_job("ss_start_lc_sell", triggered_by="Flow 4 (On-Demand)"):
                    st.toast("⚡ Started 'Place Pre-Open LC Sell'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:00 IST • Pre-Open LC Order")
        with c2:
            if st.button("🔍 Query Pre-Open IEP Prices", use_container_width=True, key="btn_flow_fetch_indicative_prices", help="Query live NSE & BSE indicative pre-open prices & buyer/seller depth"):
                if job_manager.run_job("fetch_indicative_prices", triggered_by="Flow 4 (On-Demand)"):
                    st.toast("🔍 Started 'Query Pre-Open IEP Prices'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:30 IST • Indicative Price Depth")
        with c3:
            if st.button("🛑 IEP Loss Check & Cancel LC", use_container_width=True, key="btn_flow_cancel_sale_order_if_loss", help="Checks IEP price and cancels LC order if loss limit exceeded"):
                if job_manager.run_job("cancel_sale_order_if_loss", triggered_by="Flow 4 (On-Demand)"):
                    st.toast("🛑 Started 'IEP Loss Check & Cancel LC'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 09:32 IST • Risk Guard Cancellation")

    # ── Flow 5: Market Hours & Afternoon Execution (10:00 - 15:30) ──
    with flow_tab5:
        st.markdown("""
        <div style="background:rgba(168, 85, 247, 0.08); border-left:4px solid #a855f7; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.84rem; color:#cbd5e1;">
            <b>Flow Stage 5: Market Hours & Afternoon Execution (10:00 – 15:30 IST)</b><br>
            Executes regular session sell strategies (UC hold, stepped GTT), records official listing gains into General.xlsx, and submits closing IPO bids.
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🎯 Regular Session Sell Strategy", use_container_width=True, key="btn_flow_regular_session_ipo_sell", help="Executes regular session IPO selling (buyer/seller ratio, UC hold & stepped GTT)"):
                if job_manager.run_job("regular_session_ipo_sell", triggered_by="Flow 5 (On-Demand)"):
                    st.toast("🎯 Started 'Regular Session Sell Strategy'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 10:01 IST • Live Session Seller")
        with c2:
            if st.button("🏆 Record Listing Results", use_container_width=True, key="btn_flow_listing_result", help="Checks official listing prices vs issue prices and updates column D in General.xlsx"):
                if job_manager.run_job("listing_result", triggered_by="Flow 5 (On-Demand)"):
                    st.toast("🏆 Started 'Record Listing Results'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 10:05 IST • Performance Audit")
        with c3:
            if st.button("📝 Submit Closing IPO Bids", use_container_width=True, key="btn_flow_ipo_application", help="Submits UPI/ASBA IPO applications via Kotak NetBanking for IPOs closing today"):
                if job_manager.run_job("ipo_application", triggered_by="Flow 5 (On-Demand)"):
                    st.toast("📝 Started 'Submit Closing IPO Bids'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⏰ 14:50 IST (Closing Day Window)")

    # ── Flow 6: System, Database & Diagnostics ──
    with flow_tab6:
        st.markdown("""
        <div style="background:rgba(203, 213, 225, 0.08); border-left:4px solid #94a3b8; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:0.84rem; color:#cbd5e1;">
            <b>Flow Stage 6: Database Synchronization, Accounts & System Diagnostics</b><br>
            Maintains the dual-tier SQLite database engine, synchronizes user profiles with Master.xlsx, and sends diagnostic notification pings.
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🗄️ Dual-Tier SQLite & Excel Sync", use_container_width=True, key="btn_flow_sync_database", help="Initializes SQLite WAL engine and synchronizes all tables with Excel"):
                if job_manager.run_job("sync_database", triggered_by="Flow 6 (On-Demand)"):
                    st.toast("🗄️ Started 'Dual-Tier SQLite Sync'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⚡ Database • SQLite WAL & Excel Sync")
        with c2:
            if st.button("👥 Sync Master User Profiles", use_container_width=True, key="btn_flow_sync_master", help="Sync Master.xlsx user profiles, client IDs & PANs with active credentials"):
                if job_manager.run_job("sync_master", triggered_by="Flow 6 (On-Demand)"):
                    st.toast("👥 Started 'Sync Master User Profiles'!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⚡ Accounts • Master.xlsx Sync")
        with c3:
            if st.button("📲 Send Telegram Test Push", use_container_width=True, key="btn_flow_telegram_test_alert", help="Dispatch diagnostic test push notification to configured Telegram Chat ID"):
                if job_manager.run_job("telegram_test_alert", triggered_by="Flow 6 (On-Demand)"):
                    st.toast("📲 Sent Telegram Test Notification!")
                    st.rerun()
                else:
                    st.warning("Job is already running. Please wait.")
            st.caption("⚡ Diagnostics • Telegram Alert Test")

# -----------------------------------------------------------------------------
# Main Application Layout: Split between Main Content & Right-Side Jobs Log Panel
# -----------------------------------------------------------------------------
if show_right_panel:
    main_col, right_col = st.columns([2.55, 1.45], gap="large")
else:
    main_col = st.container()
    right_col = None

with main_col:
    @st.fragment(run_every=auto_refresh_sec)
    def render_active_view():
        users, df_sme_raw, df_mb_raw, df_sme_clean, df_mb_clean, df_all_ipos, df_allotments, df_master, df_recent_active, df_applied, applied_lookup = load_all_dashboard_data()

        # -----------------------------------------------------------------------------
        # TAB 1: Executive Dashboard
        # -----------------------------------------------------------------------------
        if nav == "📊 Executive Dashboard":
            st.markdown("<div class='section-head'>📊 Executive Summary & System Overview</div>", unsafe_allow_html=True)

            kpi1, kpi2, kpi3 = st.columns(3)

            with kpi1:
                total_valuation = df_master['current_value'].dropna().sum() if not df_master.empty and 'current_value' in df_master.columns else 0.0
                st.markdown(f"""
                <div class="glass-card">
                    <div class="kpi-title">Total Account Valuation</div>
                    <div class="kpi-value text-emerald">₹{total_valuation:,.2f}</div>
                    <div class="kpi-footer">Synced from Master.xlsx</div>
                </div>
                """, unsafe_allow_html=True)

            with kpi2:
                allotment_cnt = len(df_allotments) if not df_allotments.empty else 0
                st.markdown(f"""
                <div class="glass-card">
                    <div class="kpi-title">Allotted Securities</div>
                    <div class="kpi-value text-amber">{allotment_cnt}</div>
                    <div class="kpi-footer">Active Allotment Portfolio</div>
                </div>
                """, unsafe_allow_html=True)

            with kpi3:
                total_ipos = len(df_all_ipos)
                st.markdown(f"""
                <div class="glass-card">
                    <div class="kpi-title">IPOs Tracked in DB</div>
                    <div class="kpi-value text-cyan">{total_ipos}</div>
                    <div class="kpi-footer">{len(df_mb_clean)} MB / {len(df_sme_clean)} SME</div>
                </div>
                """, unsafe_allow_html=True)

            # Section: Real-Time Job Scheduler & On-Demand Controller
            st.markdown("<div class='section-head'>⚡ On-Demand Controls & Job Execution</div>", unsafe_allow_html=True)
            if not show_right_panel:
                render_live_job_status_and_output(show_output_box=True)
                st.markdown("<br>", unsafe_allow_html=True)
            render_on_demand_buttons()
            st.markdown("---")

            # Section: IPOs Closing Today & Schedule
            today_day = datetime.date.today().day
            st.markdown(f"<div class='section-head'>⏰ Active IPO Schedule & Closing Filter (Today: Day {today_day})</div>", unsafe_allow_html=True)

            recent_days = sorted([int(d) for d in df_recent_active['Close Day'].unique() if d > 0])
            upcoming_days = [d for d in recent_days if d >= today_day]

            fcol1, fcol2 = st.columns([1, 2])
            with fcol1:
                opts = [f"Today (Day {today_day})", "Active Recent IPOs (Last 10)", "All Database Records"] + [f"Day {d}" for d in recent_days]
                selected_view = st.selectbox("Select Closing View", opts, index=0, key="closing_view_select")

            if selected_view.startswith("Today"):
                df_closing_show = df_recent_active[df_recent_active['Close Day'] == today_day]
                if df_closing_show.empty:
                    next_day_str = f"Day {upcoming_days[0]}" if upcoming_days else "N/A"
                    st.info(f"ℹ️ No active IPOs scheduled to close on exact Day {today_day} in the last 10 entries of General.xlsx. Next upcoming active closing date is **{next_day_str}**:")
                    if upcoming_days:
                        df_closing_show = df_recent_active[df_recent_active['Close Day'] == upcoming_days[0]]
            elif selected_view == "Active Recent IPOs (Last 10)":
                df_closing_show = df_recent_active[df_recent_active['Close Day'] > 0]
            elif selected_view == "All Database Records":
                df_closing_show = df_all_ipos
            else:
                target_day = int(selected_view.replace("Day ", ""))
                df_closing_show = df_recent_active[df_recent_active['Close Day'] == target_day]

            if not df_closing_show.empty:
                df_closing_show = df_closing_show.copy()

                def _get_user_app_summary(row):
                    comp_name = clean_company_name(str(row.get('Company Name', ''))).lower()
                    status_parts = []
                    for u in users:
                        uci_str = str(u.get('uci'))
                        u_name = u.get('name', f"User {uci_str}")
                        rec = applied_lookup.get((uci_str, comp_name))
                        if not rec:
                            for (r_uci, r_ipo), r_data in applied_lookup.items():
                                if r_uci == uci_str and (r_ipo in comp_name or comp_name in r_ipo):
                                    rec = r_data
                                    break
                        if rec:
                            if rec.get("Status") == "FAILED":
                                fail_reason = rec.get("Failure Reason", "Failed")
                                status_parts.append(f"{u_name}: ❌ ({fail_reason})")
                            else:
                                amt = rec.get("Total Amount (₹)", 0.0)
                                amt_label = f"₹{amt/100000:.2f}L" if amt >= 100000 else f"₹{amt:,.0f}"
                                lots_str = rec.get("Lots / Quantity", "1 Lot")
                                status_parts.append(f"{u_name}: ✅ {lots_str} ({amt_label})")
                        else:
                            status_parts.append(f"{u_name}: ⏳ Pending")
                    return "  |  ".join(status_parts)

                df_closing_show['User Applications'] = df_closing_show.apply(_get_user_app_summary, axis=1)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Total IPOs Displayed", len(df_closing_show))
                with c2:
                    apply_recs = len(df_closing_show[df_closing_show['Apply Recommendation'].str.contains('Apply')])
                    st.metric("Apply Recommended", f"{apply_recs} / {len(df_closing_show)}")
                with c3:
                    max_gmp = df_closing_show['GMP (₹)'].max()
                    st.metric("Max GMP", f"₹{max_gmp:.2f}")

                st.dataframe(
                    df_closing_show[['Company Name', 'Category', 'Total Score', 'Apply Recommendation', 'User Applications', 'GMP (₹)', 'Listing Gain %', 'Retail Sub (x)', 'Close Date']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No IPO records found matching the selected filter.")

            # ── Sub-Section: User-Wise Applied IPOs & Execution Status ──
            st.markdown("<br><div class='section-head'>👥 User-Wise Applied IPOs, Allocations & Execution Status</div>", unsafe_allow_html=True)
            st.caption("Comprehensive user-by-user audit of all applied IPOs, applied amounts, lots/shares, and live execution status (including failure diagnosis).")

            if not df_applied.empty:
                col_filt1, col_filt2 = st.columns([1.5, 2])
                with col_filt1:
                    user_filter_options = ["All Users (Consolidated)"] + [f"User {u.get('uci')}: {u.get('name')}" for u in users] + ["⚠️ Failures Only"]
                    selected_user_filter = st.selectbox("Filter Applications by User", user_filter_options, key="select_user_app_filter")
                with col_filt2:
                    filter_to_closing = st.checkbox("Focus only on displayed closing view IPOs", value=False, key="check_filter_closing_ipos")

                df_app_display = df_applied.copy()

                if filter_to_closing and not df_closing_show.empty:
                    closing_ipo_names = [clean_company_name(str(n)).lower() for n in df_closing_show['Company Name']]
                    df_app_display = df_app_display[df_app_display['IPO Name'].str.lower().apply(lambda x: any(c in x or x in c for c in closing_ipo_names))]

                if selected_user_filter == "⚠️ Failures Only":
                    df_app_display = df_app_display[df_app_display['Status'] == 'FAILED']
                elif selected_user_filter != "All Users (Consolidated)":
                    sel_uci = selected_user_filter.split(":")[0].replace("User", "").strip()
                    df_app_display = df_app_display[df_app_display['UCI'] == sel_uci]

                # Metric Cards
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Total Bids / Applications", len(df_app_display))
                with m2:
                    tot_amt = df_app_display['Total Amount (₹)'].sum() if not df_app_display.empty else 0.0
                    st.metric("Total Capital Applied", f"₹{tot_amt:,.2f}")
                with m3:
                    succ_bids = len(df_app_display[df_app_display['Status'] == 'APPLIED']) if not df_app_display.empty else 0
                    st.metric("Successful Applications", f"{succ_bids} / {len(df_app_display)}")
                with m4:
                    fail_bids = len(df_app_display[df_app_display['Status'] == 'FAILED']) if not df_app_display.empty else 0
                    if fail_bids > 0:
                        st.markdown(f"""
                        <div class="glass-card" style="padding:10px 14px; border-left:4px solid #ef4444; margin-top:2px;">
                            <div style="font-size:0.75rem; color:#f87171; font-weight:700;">⚠️ ACTIVE FAILURES</div>
                            <div style="font-size:1.25rem; font-weight:800; color:#ef4444;">{fail_bids} Failed</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="glass-card" style="padding:10px 14px; border-left:4px solid #10b981; margin-top:2px;">
                            <div style="font-size:0.75rem; color:#34d399; font-weight:700;">✅ ALL CLEAN</div>
                            <div style="font-size:1.25rem; font-weight:800; color:#10b981;">0 Failures</div>
                        </div>
                        """, unsafe_allow_html=True)

                # Active Failure Diagnosis Alerts
                failures = df_app_display[df_app_display['Status'] == 'FAILED']
                if not failures.empty:
                    for _, f_row in failures.iterrows():
                        st.error(
                            f"🚨 **Application Failure Alert**: **{f_row['Account']}** failed applying to **{f_row['IPO Name']}** "
                            f"(Lots: `{f_row['Lots / Quantity']}`, Amount: `₹{f_row['Total Amount (₹)']:,.2f}`).\n\n"
                            f"**Failure Reason:** `{f_row['Failure Reason']}` | **Date:** `{f_row['Applied Date']}`"
                        )
                    if st.button("🔁 Trigger Re-Application for Closing IPOs", key="btn_retry_failed_ipos", help="Execute on-demand IPO application routine via Kotak NetBanking"):
                        if job_manager.run_job("ipo_application", triggered_by="Dashboard (Retry Failures)"):
                            st.toast("🚀 Started IPO Re-Application job in background!")
                            st.rerun()

                # User Applications Table
                st.dataframe(
                    df_app_display[[
                        'Account', 'IPO Name', 'Category', 'Lots / Quantity',
                        'Issue Price (₹)', 'Total Amount (₹)', 'Status',
                        'Failure Reason', 'Applied Date'
                    ]],
                    column_config={
                        "Issue Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                        "Total Amount (₹)": st.column_config.NumberColumn(format="₹%,.2f"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No applied IPO records found yet in IPO-applied.xlsx or database.")



        # -----------------------------------------------------------------------------
        # TAB: Job Scheduler & Live Controls
        # -----------------------------------------------------------------------------
        elif nav == "⚡ Job Scheduler & Live Controls":
            st.markdown("<div class='section-head'>⚡ Real-Time Job Scheduler & On-Demand Controller</div>", unsafe_allow_html=True)
            st.markdown("""
            Monitor live executing jobs with start timestamps and elapsed duration, track upcoming schedule countdowns,
            inspect real-time job execution logs, and trigger automation workflows on-demand.
            """)

            # 1. Live Status & Output Stream (auto-refreshes every 3 seconds via @st.fragment)
            render_live_job_status_and_output(show_output_box=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 2. On-Demand Job Execution Controller
            render_on_demand_buttons()

            st.markdown("---")

            # 3. Daily Automation Schedule Reference
            st.markdown("<div class='section-head'>📅 Complete Daily Automation Schedule (16 Tasks)</div>", unsafe_allow_html=True)

            schedule_data = [
                {"Time (IST)": "08:00", "Task": "Streamlit Dashboard", "Job Key": "launch_streamlit_dashboard", "Category": "System", "Description": "Initiate Streamlit control hub dashboard"},
                {"Time (IST)": "08:30", "Task": "Scrape Latest IPOs", "Job Key": "ipo_entry", "Category": "IPO & Research", "Description": "Scrape latest Chittorgarh IPO listings into General.xlsx"},
                {"Time (IST)": "08:35", "Task": "Update Dynamic Data", "Job Key": "update_dynamic_data", "Category": "IPO & Research", "Description": "Morning refresh of subscription, GMP & formula scores"},
                {"Time (IST)": "08:40", "Task": "Check IPO Allotments", "Job Key": "allotment_general", "Category": "Trading & Listing Day", "Description": "Check Zerodha holdings for newly discovered allotments"},
                {"Time (IST)": "09:00", "Task": "Pre-Open LC Sell Order", "Job Key": "ss_start_lc_sell", "Category": "Trading & Listing Day", "Description": "Place Lower Circuit sell orders for newly allotted shares today"},
                {"Time (IST)": "09:05", "Task": "Money Withdraw to Bank", "Job Key": "money_withdraw", "Category": "Funds & Banking", "Description": "Calculate IPO fund requirements and withdraw from Kite to Kotak bank"},
                {"Time (IST)": "09:10", "Task": "Bank to Kite Transfer", "Job Key": "bank_to_kite", "Category": "Funds & Banking", "Description": "Transfer excess Kotak bank balance to Zerodha Kite for SMWS"},
                {"Time (IST)": "09:15", "Task": "SMWS ETF Sell", "Job Key": "smws_seller", "Category": "Funds & Banking", "Description": "Sell SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on signal"},
                {"Time (IST)": "09:20", "Task": "Priority IPO Sell SMWS", "Job Key": "priority_ipo_sell_smws", "Category": "Funds & Banking", "Description": "Liquidate SMWS ETFs when IPO application funds are required"},
                {"Time (IST)": "09:25", "Task": "SMWS ETF Buy", "Job Key": "smws_buyer", "Category": "Funds & Banking", "Description": "Buy SMWS ETFs based on strategy sheet signal"},
                {"Time (IST)": "09:32", "Task": "Pre-Open IEP Loss Check", "Job Key": "cancel_sale_order_if_loss", "Category": "Trading & Listing Day", "Description": "Cancel pre-open LC sell orders if IEP indicates discount/loss limit exceeded"},
                {"Time (IST)": "10:01", "Task": "Regular Session Sell", "Job Key": "regular_session_ipo_sell", "Category": "Trading & Listing Day", "Description": "Execute regular session IPO selling (buyer/seller ratio & UC check)"},
                {"Time (IST)": "10:05", "Task": "Check Listing Results", "Job Key": "listing_result", "Category": "IPO & Research", "Description": "Check listing prices vs issue prices and update column D in General.xlsx"},
                {"Time (IST)": "12:05", "Task": "Mid-Day Dynamic Data", "Job Key": "update_dynamic_data", "Category": "IPO & Research", "Description": "Mid-day refresh of GMP and subscription figures"},
                {"Time (IST)": "14:47", "Task": "Pre-Close Dynamic Data", "Job Key": "update_dynamic_data", "Category": "IPO & Research", "Description": "Final pre-close subscription refresh before 3:00 PM cutoff"},
                {"Time (IST)": "14:50", "Task": "Apply Closing IPOs", "Job Key": "ipo_application", "Category": "IPO & Research", "Description": "Submit UPI IPO applications via Kotak for IPOs closing today"}
            ]
            df_sched = pd.DataFrame(schedule_data)
            st.dataframe(df_sched, use_container_width=True, hide_index=True)



        # -----------------------------------------------------------------------------
        # TAB 2: Balances & Account Manager
        # -----------------------------------------------------------------------------
        elif nav == "💰 Balances & Account Manager":
            st.markdown("<div class='section-head'>💰 Multi-Account Profiles & Capital Allocation</div>", unsafe_allow_html=True)

            if users:
                cols = st.columns(len(users))
                for idx, u in enumerate(users):
                    with cols[idx]:
                        name = u.get("name", f"User {idx+1}")
                        client_id = u.get("broker_client_id", "N/A")
                        bank_id = u.get("bank_user", "N/A")
                        pan = u.get("PAN", "N/A")
                        intraday = "Enabled" if u.get("intraday") == "1" else "Disabled"

                        # Find matching row in df_master
                        curr_val_str = "N/A"
                        if not df_master.empty and 'uci' in df_master.columns and 'current_value' in df_master.columns:
                            match_row = df_master[df_master['uci'].astype(str) == str(u.get('uci'))]
                            if not match_row.empty:
                                val = match_row.iloc[0]['current_value']
                                if pd.notnull(val):
                                    curr_val_str = f"₹{float(val):,.2f}"

                        st.markdown(f"""
                        <div class="glass-card" style="border-top: 4px solid #38bdf8;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3 style="margin:0; color:#f8fafc;">{name}</h3>
                                <span class="pill pill-blue">UCI: {u.get('uci')}</span>
                            </div>
                            <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
                            <p style="margin: 6px 0; font-size: 0.9rem; color:#94a3b8;">Broker Client ID: <b style="color:#f8fafc;">{client_id}</b></p>
                            <p style="margin: 6px 0; font-size: 0.9rem; color:#94a3b8;">PAN Reference: <b style="color:#f8fafc;">{pan}</b></p>
                            <p style="margin: 6px 0; font-size: 0.9rem; color:#94a3b8;">Intraday Mode: <b style="color:#34d399;">{intraday}</b></p>
                            <p style="margin: 6px 0; font-size: 0.9rem; color:#94a3b8;">Current Value (Master.xlsx): <b style="color:#34d399;">{curr_val_str}</b></p>
                        </div>
                        """, unsafe_allow_html=True)

            if not df_master.empty:
                st.markdown("<div class='section-head'>📋 Master User Database (Master.xlsx)</div>", unsafe_allow_html=True)
                st.dataframe(df_master, use_container_width=True, hide_index=True)

            st.markdown("<div class='section-head'>⚙️ Automated Capital Routing Rules</div>", unsafe_allow_html=True)

            r1, r2 = st.columns(2)
            with r1:
                st.markdown("""
                <div class="glass-card">
                    <h4 style="margin-top:0; color:#fbbf24;">📥 IPO Application Withdrawal Policy</h4>
                    <ul style="color:#cbd5e1; font-size:0.9rem; padding-left: 20px; line-height: 1.7;">
                        <li><b>Mainboard Budget</b>: ~₹2,09,000 required per account for closing IPOs</li>
                        <li><b>SME Budget</b>: ~₹2,80,000 required per account for closing IPOs</li>
                        <li><b>Execution Trigger</b>: Triggered daily at <b>09:05 AM</b> via Playwright script <code>fund_manager.py</code>.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with r2:
                st.markdown("""
                <div class="glass-card">
                    <h4 style="margin-top:0; color:#38bdf8;">📤 Idle Bank Fund Sweeping Policy (SMWS)</h4>
                    <ul style="color:#cbd5e1; font-size:0.9rem; padding-left: 20px; line-height: 1.7;">
                        <li>Idle cash in Kotak Bank is swept automatically into Zerodha Kite.</li>
                        <li>Transfers occur daily at <b>09:10 AM</b> via <code>fund_transfer_for_smws.py</code>.</li>
                        <li>Swept funds trade high-liquidity ETFs (<code>NIFTYIETF</code>, <code>TATAGOLD</code>, <code>TATSILV</code>).</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # TAB 3: IPO Funding & Margin Calculator
        # -----------------------------------------------------------------------------
        elif nav == "🧮 IPO Funding & Margin Calculator":
            st.markdown("<div class='section-head'>🧮 Interactive Application Funding Calculator</div>", unsafe_allow_html=True)

            calc_col1, calc_col2 = st.columns([1, 1.2])

            with calc_col1:
                st.markdown("#### Input Parameters")
                num_accounts = st.slider("Number of Account Applications", min_value=1, max_value=max(len(users), 10), value=len(users))
                mb_count = st.number_input("Mainboard IPOs Closing Today", min_value=0, max_value=10, value=1)
                sme_count = st.number_input("SME IPOs Closing Today", min_value=0, max_value=10, value=0)

                custom_kotak_bal = st.number_input("Estimated Current Kotak Bank Balance per Account (₹)", value=50000, step=10000)

            with calc_col2:
                mb_cost_per_app = 209000
                sme_cost_per_app = 280000

                req_per_account = (mb_count * mb_cost_per_app) + (sme_count * sme_cost_per_app)
                total_req_all_accounts = req_per_account * num_accounts

                total_kotak_avail = custom_kotak_bal * num_accounts
                shortfall_per_account = max(0, req_per_account - custom_kotak_bal)
                total_withdrawal_needed = shortfall_per_account * num_accounts

                st.markdown(f"""
                <div class="glass-card" style="border: 1px solid rgba(56, 189, 248, 0.4);">
                    <h4 style="margin-top:0; color:#38bdf8;">Fund Requirement Calculation</h4>
                    <hr style="border-color: rgba(255,255,255,0.08);">
                    <p style="font-size:1.05rem;">Required per Account: <b style="color:#f8fafc;">₹{req_per_account:,.2f}</b></p>
                    <p style="font-size:1.25rem;">Total Required Across ({num_accounts} Accounts): <b class="text-amber">₹{total_req_all_accounts:,.2f}</b></p>
                    <hr style="border-color: rgba(255,255,255,0.08);">
                    <p style="font-size:1.05rem;">Est. Total Kotak Bank Balance: <b style="color:#34d399;">₹{total_kotak_avail:,.2f}</b></p>
                    <p style="font-size:1.3rem;">Zerodha -> Kotak Withdrawal Needed: <b class="text-rose">₹{total_withdrawal_needed:,.2f}</b></p>
                </div>
                """, unsafe_allow_html=True)

                if total_withdrawal_needed > 0:
                    st.warning(f"⚠️ Action Required: Initiate withdrawal of ₹{shortfall_per_account:,.2f} per account from Zerodha to Kotak Bank before 02:50 PM.")
                else:
                    st.success("✅ Sufficient Kotak Bank balance available for today's IPO applications!")

        # -----------------------------------------------------------------------------
        # TAB 4: IPO Analytics & Predictions
        # -----------------------------------------------------------------------------
        elif nav == "🚀 IPO Analytics & Predictions":
            st.markdown("<div class='section-head'>🚀 Comprehensive IPO Analytics & Predictions</div>", unsafe_allow_html=True)

            subtab0, subtab1, subtab2, subtab3 = st.tabs(["⏰ Closing Today", "🏛️ Mainboard IPOs", "🏢 SME IPOs", "🔥 High Gain (>20% GMP)"])

            display_cols = ['Company Name', 'Category', 'Total Score', 'Apply Recommendation', 'GMP (₹)', 'Listing Gain %', 'Retail Sub (x)', 'Close Date']

            with subtab0:
                st.subheader(f"IPOs Closing Today (Day {datetime.date.today().day}) - Last 10 Entries")
                df_today_show = df_recent_active[df_recent_active['Is Closing Today']] if not df_recent_active.empty else pd.DataFrame()
                if not df_today_show.empty:
                    st.dataframe(df_today_show[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info(f"No active IPOs closing today (Day {datetime.date.today().day}) found in the last 10 entries of General.xlsx.")

            with subtab1:
                st.subheader("Mainboard IPO Listings")
                search_mb = st.text_input("Search Mainboard IPO Name", key="search_mb_main")
                df_mb_show = df_mb_clean
                if search_mb and not df_mb_show.empty:
                    df_mb_show = df_mb_show[df_mb_show['Company Name'].str.contains(search_mb, case=False)]
                st.dataframe(df_mb_show[display_cols] if not df_mb_show.empty else df_mb_show, use_container_width=True, hide_index=True)

            with subtab2:
                st.subheader("SME IPO Listings")
                search_sme = st.text_input("Search SME IPO Name", key="search_sme_main")
                df_sme_show = df_sme_clean
                if search_sme and not df_sme_show.empty:
                    df_sme_show = df_sme_show[df_sme_show['Company Name'].str.contains(search_sme, case=False)]
                st.dataframe(df_sme_show[display_cols] if not df_sme_show.empty else df_sme_show, use_container_width=True, hide_index=True)

            with subtab3:
                st.subheader("High Premium IPOs (>20% Listing Gain)")
                df_hot = df_all_ipos[df_all_ipos['Listing Gain %'] >= 20.0] if not df_all_ipos.empty else pd.DataFrame()
                if not df_hot.empty:
                    st.dataframe(df_hot[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("No IPOs currently meeting the >20% listing gain threshold.")

        # -----------------------------------------------------------------------------
        # TAB 5: Live SMWS Strategy Monitor
        # -----------------------------------------------------------------------------
        elif nav == "📈 Live SMWS Strategy Monitor":
            st.markdown("<div class='section-head'>📈 Systematic Market & Withdrawal Strategy (SMWS) Monitor</div>", unsafe_allow_html=True)

            signals = fetch_smws_signals()

            if "error" in signals:
                st.error(f"❌ Error fetching Google Sheet: {signals['error']}")
                st.info("💡 Tip: Ensure the sheet is published to web and your internet connection is stable.")
            else:
                # Show data-source badge
                if signals.get("_from_cache"):
                    st.warning(
                        f"🗄️ **Showing cached signals** (Google Sheet returned Loading... and warmer couldn't resolve it). "
                        f"Last good data: `{signals.get('_cache_time', 'unknown')}`"
                    )
                else:
                    st.success("📡 Live SMWS Signals fetched directly from Strategy Google Sheet.")

                sig_c1, sig_c2, sig_c3 = st.columns(3)

                def format_signal(val, label):  # noqa: F811
                    val_str = str(val).strip()
                    if "loading" in val_str.lower() or val_str in ("nan", ""):
                        # Warmer ran but sheet still not ready — show soft amber pill
                        return '<span class="pill pill-amber">⏳ Recalculating…</span>'
                    elif val_str == "1":
                        if label.lower() == "sell":
                            return '<span class="pill pill-red">🔴 SELL SIGNAL</span>'
                        else:
                            return '<span class="pill pill-green">🟢 BUY SIGNAL</span>'
                    elif val_str == "0":
                        return '<span class="pill pill-purple">⚪ HOLD / NO SIGNAL</span>'
                    else:
                        return f'<span class="pill pill-blue">SIGNAL: {val_str}</span>'

                with sig_c1:
                    st.markdown(f"""
                    <div class="glass-card">
                        <h4 style="margin-top:0; color:#38bdf8;">NIFTYIETF</h4>
                        <p>Buy Signal: {format_signal(signals.get('buy_nifty'), 'Buy')}</p>
                        <p>Sell Signal: {format_signal(signals.get('sell_nifty'), 'Sell')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with sig_c2:
                    st.markdown(f"""
                    <div class="glass-card">
                        <h4 style="margin-top:0; color:#fbbf24;">TATAGOLD</h4>
                        <p>Buy Signal: {format_signal(signals.get('buy_gold'), 'Buy')}</p>
                        <p>Sell Signal: {format_signal(signals.get('sell_gold'), 'Sell')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with sig_c3:
                    st.markdown(f"""
                    <div class="glass-card">
                        <h4 style="margin-top:0; color:#c084fc;">TATSILV</h4>
                        <p>Buy Signal: {format_signal(signals.get('buy_silver'), 'Buy')}</p>
                        <p>Sell Signal: {format_signal(signals.get('sell_silver'), 'Sell')}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # -----------------------------------------------------------------------------
        # TAB 6: Allotted Holdings Tracker
        # -----------------------------------------------------------------------------
        elif nav == "📦 Allotted Holdings Tracker":
            st.markdown("<div class='section-head'>📦 Detected IPO Allotment Portfolio</div>", unsafe_allow_html=True)

            if not df_allotments.empty:
                cnt = len(df_allotments)
                st.metric("Total Active Allotments Recorded", cnt)

                st.dataframe(
                    df_allotments[['uci', 'security_name', 'lot_size', 'issue_price', 'shares_allocated', 'stock_category', 'special_session_status']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No active holdings found in allotted_holdings.xlsx.")

        # -----------------------------------------------------------------------------
        # TAB 7: System Health & Activity Logs
        # -----------------------------------------------------------------------------
        elif nav == "📜 System Health & Activity Logs":
            st.markdown("<div class='section-head'>📜 System Health Diagnostics & Real-time Logs</div>", unsafe_allow_html=True)

            st.markdown("#### System Component Health Checks")
            h1, h2, h3, h4 = st.columns(4)

            env_exists = os.path.exists(os.path.join(BASE_DIR, ".env"))
            gen_exists = os.path.exists(os.path.join(BASE_DIR, "General.xlsx"))
            master_exists = os.path.exists(os.path.join(BASE_DIR, "Master.xlsx"))
            allot_exists = os.path.exists(os.path.join(BASE_DIR, "allotted_holdings.xlsx"))

            env_badge = '<span class="pill pill-green">Found</span>' if env_exists else '<span class="pill pill-amber">Missing</span>'
            gen_badge = '<span class="pill pill-green">Found</span>' if gen_exists else '<span class="pill pill-amber">Missing</span>'
            master_badge = '<span class="pill pill-green">Found</span>' if master_exists else '<span class="pill pill-amber">Missing</span>'
            allot_badge = '<span class="pill pill-green">Found</span>' if allot_exists else '<span class="pill pill-amber">Missing</span>'
            net_badge = '<span class="pill pill-green">Online</span>' if internet_ok else '<span class="pill pill-amber">Offline</span>'

            with h1:
                st.markdown(f"<b>.env Credentials File</b>: {env_badge}", unsafe_allow_html=True)
            with h2:
                st.markdown(f"<b>General.xlsx Database</b>: {gen_badge}<br><b>Master.xlsx Database</b>: {master_badge}", unsafe_allow_html=True)
            with h3:
                st.markdown(f"<b>Allotted Holdings File</b>: {allot_badge}", unsafe_allow_html=True)
            with h4:
                st.markdown(f"<b>Internet Connection</b>: {net_badge}", unsafe_allow_html=True)

            # ── Telegram Push Notification Health & Tester ──
            st.markdown("---")
            st.markdown("#### 📲 Telegram Push Notification Control & Diagnostics")

            tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
            tg_configured = bool(tg_token and tg_chat)

            tg_status_badge = '<span class="pill pill-green">Configured</span>' if tg_configured else '<span class="pill pill-amber">Not Configured</span>'

            tg_col1, tg_col2 = st.columns([2, 1])
            with tg_col1:
                st.markdown(f"<b>Telegram Bot Status</b>: {tg_status_badge}", unsafe_allow_html=True)
                if tg_configured:
                    masked_token = tg_token[:6] + "..." + tg_token[-4:] if len(tg_token) > 10 else "***"
                    st.caption(f"Bot Token: `{masked_token}` | Chat ID: `{tg_chat}`")
                else:
                    st.info("💡 To enable push notifications on your phone, add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to your `.env` file.")

            with tg_col2:
                if st.button("🧪 Send Test Telegram Alert"):
                    from common_foundation import send_telegram_notification
                    test_msg = (
                        "🧪 <b>CapitalFund1 Test Push Notification</b>\n\n"
                        "✅ Your Telegram Bot integration is working perfectly!\n"
                        f"⏰ <b>Timestamp</b>: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
                    )
                    success = send_telegram_notification(test_msg)
                    if success:
                        st.success("✅ Test notification sent! Check your Telegram app.")
                    else:
                        st.error("❌ Failed to send. Please check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.")

            st.markdown("---")
            st.markdown("#### Live Console Output Viewer")

            l_source = st.radio("Log Source File", ["logs/error.log", "system.txt"], horizontal=True)
            l_type = "error" if "error" in l_source else "system"

            lines = read_logs(l_type)

            filter_txt = st.text_input("Filter Log Line Keyword", "")
            if filter_txt:
                lines = [line for line in lines if filter_txt.lower() in line.lower()]

            log_body = "".join(lines)
            st.markdown(f"<div class='console-box'>{log_body}</div>", unsafe_allow_html=True)

            st.download_button(
                label="📥 Download Current Log File",
                data=log_body,
                file_name=f"capitalfund1_{l_type}_log.txt",
                mime="text/plain"
            )

    render_active_view()

if right_col is not None:
    with right_col:
        render_jobs_log_side_panel()
