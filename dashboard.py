import os
import sys
import re
import time

import datetime
import json
import pandas as pd
import openpyxl
import streamlit as st

# Ensure project root & src are in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

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
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loaders with Caching
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_ipo_database():
    excel_path = os.path.join(BASE_DIR, "General.xlsx")
    if not os.path.exists(excel_path):
        return pd.DataFrame(), pd.DataFrame()
    try:
        df_sme = pd.read_excel(excel_path, sheet_name="IPOSME")
        df_mb = pd.read_excel(excel_path, sheet_name="IPOMB")
        return df_sme, df_mb
    except Exception as e:
        st.error(f"Error loading General.xlsx: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=60)
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

@st.cache_data(ttl=30)
def fetch_smws_signals():
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSs2i_IJgQNpj8_gd4OMMQvvMh-G2iO15FPlMm-x3Z8lYTjX0-BePODzuXzTKq-bFZZHmyqCueCtx-5/pub?gid=614695683&single=true&output=csv"
    try:
        df = pd.read_csv(url_csv)
        buy_nifty = str(df.iloc[23, 4]).strip() if len(df) > 23 else "Loading..."
        buy_gold = str(df.iloc[26, 4]).strip() if len(df) > 26 else "Loading..."
        buy_silver = str(df.iloc[29, 4]).strip() if len(df) > 29 else "Loading..."
        
        sell_nifty = str(df.iloc[24, 4]).strip() if len(df) > 24 else "Loading..."
        sell_gold = str(df.iloc[27, 4]).strip() if len(df) > 27 else "Loading..."
        sell_silver = str(df.iloc[30, 4]).strip() if len(df) > 30 else "Loading..."
        
        return {
            "buy_nifty": buy_nifty, "buy_gold": buy_gold, "buy_silver": buy_silver,
            "sell_nifty": sell_nifty, "sell_gold": sell_gold, "sell_silver": sell_silver,
            "raw_df": df
        }
    except Exception as e:
        return {"error": str(e)}

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
st.sidebar.subheader("Quick Operations")
if st.sidebar.button("🔄 Refresh All Data"):
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

# Load global datasets
users = load_credentials()
df_sme_raw, df_mb_raw = load_ipo_database()
df_sme_clean = clean_ipo_dataframe(df_sme_raw, "SME")
df_mb_clean = clean_ipo_dataframe(df_mb_raw, "Mainboard")
df_all_ipos = pd.concat([df_mb_clean, df_sme_clean], ignore_index=True)
df_allotments = load_allotted_holdings()

# -----------------------------------------------------------------------------
# TAB 1: Executive Dashboard
# -----------------------------------------------------------------------------
if nav == "📊 Executive Dashboard":
    st.markdown("<div class='section-head'>📊 Executive Summary & System Overview</div>", unsafe_allow_html=True)
    
    kpi1, kpi2 = st.columns(2)
    
    with kpi1:
        allotment_cnt = len(df_allotments) if not df_allotments.empty else 0
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-title">Allotted Securities</div>
            <div class="kpi-value text-amber">{allotment_cnt}</div>
            <div class="kpi-footer">Active Allotment Portfolio</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        total_ipos = len(df_all_ipos)
        st.markdown(f"""
        <div class="glass-card">
            <div class="kpi-title">IPOs Tracked in DB</div>
            <div class="kpi-value text-cyan">{total_ipos}</div>
            <div class="kpi-footer">{len(df_mb_clean)} MB / {len(df_sme_clean)} SME</div>
        </div>
        """, unsafe_allow_html=True)

    # Section: IPOs Closing Today & Schedule
    today_day = datetime.date.today().day
    st.markdown(f"<div class='section-head'>⏰ Active IPO Schedule & Closing Filter (Today: Day {today_day})</div>", unsafe_allow_html=True)
    
    # Extract active recent IPOs (strictly last 10 records of each category in General.xlsx)
    df_sme_last10 = clean_ipo_dataframe(df_sme_raw.tail(10), "SME") if not df_sme_raw.empty else pd.DataFrame()
    df_mb_last10 = clean_ipo_dataframe(df_mb_raw.tail(10), "Mainboard") if not df_mb_raw.empty else pd.DataFrame()
    df_recent_active = pd.concat([df_mb_last10, df_sme_last10], ignore_index=True) if (not df_sme_last10.empty or not df_mb_last10.empty) else df_all_ipos

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
            df_closing_show[['Company Name', 'Category', 'Total Score', 'Apply Recommendation', 'GMP (₹)', 'Listing Gain %', 'Retail Sub (x)', 'Close Date']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No IPO records found matching the selected filter.")



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
                </div>
                """, unsafe_allow_html=True)

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
    
    st.info("📡 Live SMWS Signals fetched directly from Strategy Google Sheet.")
    
    signals = fetch_smws_signals()
    
    if "error" in signals:
        st.error(f"Error fetching Google Sheet: {signals['error']}")
    else:
        sig_c1, sig_c2, sig_c3 = st.columns(3)
        
        def format_signal(val, label):
            if "Loading" in str(val):
                return f'<span class="pill pill-amber">⏳ Sheet Recalculating ({val})</span>'
            elif str(val) == "1":
                return f'<span class="pill pill-green">🟢 BUY SIGNAL (1)</span>'
            elif str(val) == "0":
                return f'<span class="pill pill-purple">⚪ HOLD / NO SIGNAL (0)</span>'
            else:
                return f'<span class="pill pill-blue">SIGNAL: {val}</span>'

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
    allot_exists = os.path.exists(os.path.join(BASE_DIR, "allotted_holdings.xlsx"))
    
    env_badge = '<span class="pill pill-green">Found</span>' if env_exists else '<span class="pill pill-amber">Missing</span>'
    gen_badge = '<span class="pill pill-green">Found</span>' if gen_exists else '<span class="pill pill-amber">Missing</span>'
    allot_badge = '<span class="pill pill-green">Found</span>' if allot_exists else '<span class="pill pill-amber">Missing</span>'
    net_badge = '<span class="pill pill-green">Online</span>' if internet_ok else '<span class="pill pill-amber">Offline</span>'

    with h1:
        st.markdown(f"<b>.env Credentials File</b>: {env_badge}", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<b>General.xlsx Database</b>: {gen_badge}", unsafe_allow_html=True)
    with h3:
        st.markdown(f"<b>Allotted Holdings File</b>: {allot_badge}", unsafe_allow_html=True)
    with h4:
        st.markdown(f"<b>Internet Connection</b>: {net_badge}", unsafe_allow_html=True)
        
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
