"""
job_manager.py
==============
Centralized job orchestration, state tracking, and output capture for CapitalFund1.
Coordinates both automated schedule triggers (common_schedule_all.py) and on-demand
Streamlit dashboard triggers.

Provides:
  - Timestamped tracking of currently executing background jobs.
  - Calculation and countdown of the next upcoming scheduled job.
  - Live execution output capture into logs/current_job.log.
  - On-demand execution helpers with thread safety and duplicate-run protection.
"""

import os
import sys
import time
import json
import threading
import datetime
from typing import Dict, Any, List, Optional
import io
import contextlib

# Ensure src in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
STATE_FILE = os.path.join(LOGS_DIR, "job_state.json")
CURRENT_JOB_LOG = os.path.join(LOGS_DIR, "current_job.log")

os.makedirs(LOGS_DIR, exist_ok=True)

# ── Job Registry Definition ──────────────────────────────────────────────────
# Defines metadata, scheduled time(s), and human-readable names for all system jobs.
JOB_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ipo_entry": {
        "name": "Scrape Latest IPOs",
        "schedule_time": ["08:30"],
        "description": "Scrape latest IPOs from Chittorgarh into General.xlsx",
        "category": "IPO & Research",
        "icon": "🚀",
    },
    "update_dynamic_data": {
        "name": "Update Dynamic Data & GMP",
        "schedule_time": ["08:35", "12:05", "14:47"],
        "description": "Refresh subscription, GMP, and dynamic data in General.xlsx",
        "category": "IPO & Research",
        "icon": "📊",
    },
    "allotment_general": {
        "name": "Check IPO Allotments",
        "schedule_time": ["08:40"],
        "description": "Check Zerodha holdings for new allotments & update allotted_holdings.xlsx",
        "category": "Trading & Listing Day",
        "icon": "📋",
    },
    "ss_start_lc_sell": {
        "name": "Pre-Open LC Sell Order",
        "schedule_time": ["09:00"],
        "description": "Place LC sell orders for newly allotted IPO shares today",
        "category": "Trading & Listing Day",
        "icon": "⚡",
    },
    "money_withdraw": {
        "name": "Money Withdraw to Bank",
        "schedule_time": ["09:05"],
        "description": "Calculate IPO fund requirements and withdraw from Kite to Kotak bank",
        "category": "Funds & Banking",
        "icon": "💸",
    },
    "bank_to_kite": {
        "name": "Bank to Kite Transfer",
        "schedule_time": ["09:10"],
        "description": "Transfer excess Kotak bank balance to Zerodha Kite for SMWS",
        "category": "Funds & Banking",
        "icon": "🏦",
    },
    "smws_seller": {
        "name": "SMWS ETF Sell",
        "schedule_time": ["09:15"],
        "description": "Sell SMWS ETFs (NIFTYIETF, TATAGOLD, TATSILV) based on signal",
        "category": "Funds & Banking",
        "icon": "📉",
    },
    "priority_ipo_sell_smws": {
        "name": "Priority IPO Sell SMWS",
        "schedule_time": ["09:20"],
        "description": "Liquidate SMWS ETFs when IPO application funds are required",
        "category": "Funds & Banking",
        "icon": "⚠️",
    },
    "smws_buyer": {
        "name": "SMWS ETF Buy",
        "schedule_time": ["09:25"],
        "description": "Buy SMWS ETFs based on strategy sheet signal",
        "category": "Funds & Banking",
        "icon": "📈",
    },
    "cancel_sale_order_if_loss": {
        "name": "Pre-Open IEP Loss Check & Cancel",
        "schedule_time": ["09:32"],
        "description": "Cancel pre-open LC sell orders if IEP indicates discount/loss threshold exceeded",
        "category": "Trading & Listing Day",
        "icon": "🔍",
    },
    "regular_session_ipo_sell": {
        "name": "Regular Session Sell",
        "schedule_time": ["10:01"],
        "description": "Execute regular session IPO selling strategy (buyer/seller ratio & UC check)",
        "category": "Trading & Listing Day",
        "icon": "📊",
    },
    "listing_result": {
        "name": "Check Listing Results",
        "schedule_time": ["10:05"],
        "description": "Check listing prices vs issue prices and update column D in General.xlsx",
        "category": "IPO & Research",
        "icon": "🏆",
    },
    "ipo_application": {
        "name": "Apply to Closing IPOs",
        "schedule_time": ["14:50"],
        "description": "Submit UPI IPO applications via Kotak for IPOs closing today",
        "category": "IPO & Research",
        "icon": "📝",
    },
    "sync_database": {
        "name": "Dual-Tier SQLite Sync",
        "schedule_time": [],
        "description": "Synchronize SQLite database tables bidirectional with Excel workbooks",
        "category": "Database & Sync",
        "icon": "🗄️",
    }
}

# Thread lock for in-process safety
_state_lock = threading.Lock()


# ── State Persistence Helpers ────────────────────────────────────────────────

def get_job_state() -> Dict[str, Any]:
    """Read the current job execution state from logs/job_state.json safely."""
    with _state_lock:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "running_jobs": {},
            "last_completed": None,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        }


def save_job_state(state: Dict[str, Any]) -> None:
    """Save the job execution state to logs/job_state.json atomically."""
    with _state_lock:
        try:
            state["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
            tmp_file = f"{STATE_FILE}.tmp_{os.getpid()}"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            os.replace(tmp_file, STATE_FILE)
        except Exception as e:
            try:
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
            except Exception:
                pass


def record_job_start(job_key: str, triggered_by: str = "Scheduler") -> None:
    """Record that a job has started running."""
    state = get_job_state()
    job_info = JOB_REGISTRY.get(job_key, {})
    name = job_info.get("name", job_key)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    now_ts = time.time()

    state["running_jobs"][job_key] = {
        "job_key": job_key,
        "name": name,
        "started_at": now_str,
        "started_ts": now_ts,
        "triggered_by": triggered_by,
        "status": "RUNNING"
    }
    save_job_state(state)

    # Prepend job run header to current_job.log
    try:
        with open(CURRENT_JOB_LOG, "w", encoding="utf-8") as f:
            f.write(f"=== [JOB STARTED: {name} ({job_key})] ===\n")
            f.write(f"Timestamp   : {now_str}\n")
            f.write(f"Triggered By: {triggered_by}\n")
            f.write(f"Status      : RUNNING\n")
            f.write("=" * 60 + "\n\n")
    except Exception:
        pass


def record_job_finish(job_key: str, status: str = "SUCCESS", error_msg: Optional[str] = None) -> None:
    """Record that a job has finished running."""
    state = get_job_state()
    job_record = state["running_jobs"].pop(job_key, None)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

    duration_sec = 0.0
    if job_record and "started_ts" in job_record:
        duration_sec = round(time.time() - job_record["started_ts"], 2)

    name = JOB_REGISTRY.get(job_key, {}).get("name", job_key)
    completed_record = {
        "job_key": job_key,
        "name": name,
        "started_at": job_record.get("started_at", "N/A") if job_record else "N/A",
        "finished_at": now_str,
        "duration_seconds": duration_sec,
        "status": status,
        "error_message": error_msg
    }
    state["last_completed"] = completed_record
    save_job_state(state)

    # Append job finish footer to current_job.log
    try:
        with open(CURRENT_JOB_LOG, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"=== [JOB FINISHED: {name}] ===\n")
            f.write(f"Finished At : {now_str}\n")
            f.write(f"Duration    : {duration_sec}s\n")
            f.write(f"Exit Status : {status}\n")
            if error_msg:
                f.write(f"Error Detail: {error_msg}\n")
            f.write("=" * 60 + "\n")
    except Exception:
        pass


def append_job_output(text: str) -> None:
    """Append stdout/stderr text into logs/current_job.log."""
    try:
        with open(CURRENT_JOB_LOG, "a", encoding="utf-8", errors="ignore") as f:
            f.write(text)
    except Exception:
        pass


def get_current_job_output(max_lines: int = 150) -> str:
    """Read recent lines from logs/current_job.log."""
    if not os.path.exists(CURRENT_JOB_LOG):
        return "No job execution output recorded yet."
    try:
        with open(CURRENT_JOB_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as e:
        return f"Error reading execution log: {e}"


# ── Schedule Countdown & Next Job Calculation ────────────────────────────────

def get_next_scheduled_job() -> Dict[str, Any]:
    """
    Computes the very next upcoming scheduled job from JOB_REGISTRY based on current IST time.
    Returns:
        job_key, name, scheduled_time, countdown_str, description, category
    """
    now = datetime.datetime.now()
    today_date = now.date()

    candidates = []

    for key, info in JOB_REGISTRY.items():
        times = info.get("schedule_time", [])
        if isinstance(times, str):
            times = [times]
        for t_str in times:
            try:
                hh, mm = map(int, t_str.split(":"))
                job_dt = datetime.datetime(today_date.year, today_date.month, today_date.day, hh, mm, 0)
                # If time has passed today, schedule for tomorrow
                if job_dt <= now:
                    job_dt += datetime.timedelta(days=1)
                candidates.append((job_dt, key, info, t_str))
            except Exception:
                continue

    if not candidates:
        return {
            "job_key": "none",
            "name": "No Scheduled Jobs Found",
            "scheduled_time": "N/A",
            "countdown_str": "N/A",
            "description": "",
            "category": ""
        }

    candidates.sort(key=lambda x: x[0])
    next_dt, next_key, next_info, t_str = candidates[0]

    diff = next_dt - now
    total_seconds = int(diff.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        countdown_str = f"in {hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        countdown_str = f"in {minutes}m {seconds}s"
    else:
        countdown_str = f"in {seconds}s"

    is_tomorrow = next_dt.date() > today_date
    time_display = f"{t_str} IST" + (" (Tomorrow)" if is_tomorrow else " (Today)")

    return {
        "job_key": next_key,
        "name": next_info.get("name", next_key),
        "scheduled_time": time_display,
        "target_datetime": next_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "countdown_str": countdown_str,
        "description": next_info.get("description", ""),
        "category": next_info.get("category", ""),
        "icon": next_info.get("icon", "⚡")
    }


def get_currently_running_jobs() -> List[Dict[str, Any]]:
    """
    Returns list of timestamped running jobs with live elapsed duration calculated.
    """
    state = get_job_state()
    running_list = []
    now_ts = time.time()

    for key, data in state.get("running_jobs", {}).items():
        started_ts = data.get("started_ts", now_ts)
        elapsed_sec = int(now_ts - started_ts)
        minutes = elapsed_sec // 60
        seconds = elapsed_sec % 60
        elapsed_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

        running_list.append({
            "job_key": key,
            "name": data.get("name", key),
            "started_at": data.get("started_at", "N/A"),
            "elapsed_str": elapsed_str,
            "triggered_by": data.get("triggered_by", "Unknown"),
            "status": "RUNNING"
        })

    return running_list


# ── On-Demand Job Execution Engine ───────────────────────────────────────────

class _StreamTee(io.TextIOBase):
    """Duplicates stdout/stderr to console and current_job.log."""
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, s):
        try:
            self.original_stream.write(s)
            self.original_stream.flush()
        except Exception:
            pass
        append_job_output(s)
        return len(s)

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass


def execute_job_target(job_key: str) -> None:
    """Direct dispatcher that calls the exact underlying function for a job key."""
    if job_key == "ipo_entry":
        import common_master_functions
        common_master_functions.latest_ipo_entry()

    elif job_key == "update_dynamic_data":
        import common_master_functions
        common_master_functions.dynamic_data_update()

    elif job_key == "allotment_general":
        import allotment_general
        allotment_general.ipo_allotment_manager()

    elif job_key == "ss_start_lc_sell":
        import ss_sale_order_on_lc_on_start_of_ss
        ss_sale_order_on_lc_on_start_of_ss.place_lc_sell_orders_for_allotted_today()

    elif job_key == "money_withdraw":
        import fund_manager
        fund_manager.daily_money_withdraw()

    elif job_key == "bank_to_kite":
        import fund_transfer_for_smws
        fund_transfer_for_smws.fund_trf_to_kite()

    elif job_key == "smws_seller":
        import trader_smws
        trader_smws.smws_seller()

    elif job_key == "priority_ipo_sell_smws":
        import trader_priority_ipo_smws_sell
        trader_priority_ipo_smws_sell.priority_ipo_sell_smws()

    elif job_key == "smws_buyer":
        import trader_smws
        trader_smws.smws_buyer()

    elif job_key == "cancel_sale_order_if_loss":
        import ss_Before_session_close_cancel_sale_or_not
        ss_Before_session_close_cancel_sale_or_not.sale_order_cancel_or_not()

    elif job_key == "regular_session_ipo_sell":
        import regular_session_sell
        regular_session_sell.regular_session_ipo_sell()

    elif job_key == "listing_result":
        import ipo_listing_result
        ipo_listing_result.update_listing_results()

    elif job_key == "ipo_application":
        import allotment_application_ipo
        allotment_application_ipo.ipo_application()

    elif job_key == "sync_database":
        import database
        database.init_db()
        database.import_all_from_excel()
        database.sync_all_to_excel()
        print("Dual-tier SQLite & Excel synchronization completed successfully.")

    elif job_key == "launch_streamlit_dashboard":
        import common_schedule_all
        common_schedule_all.launch_streamlit_dashboard()

    else:
        raise ValueError(f"Unknown job key '{job_key}'")


def run_job(job_key: str, triggered_by: str = "On-Demand (Dashboard)", run_in_background: bool = True) -> bool:
    """
    Executes a registered job with:
      - Duplicate execution protection (skips if already running).
      - Status tracking in logs/job_state.json.
      - Output capture into logs/current_job.log.
      - Audit logging via logger_setup.
    """
    if job_key not in JOB_REGISTRY:
        print(f"Error: Unknown job '{job_key}'")
        return False

    # Check if already running
    state = get_job_state()
    if job_key in state.get("running_jobs", {}):
        print(f"Job '{job_key}' is already running. Please wait for completion.")
        return False

    def _worker():
        record_job_start(job_key, triggered_by=triggered_by)
        error_msg = None
        status = "SUCCESS"

        try:
            from logger_setup import get_logger
            logger = get_logger("job_manager")
            logger.audit(f"[AUDIT] Job Started: {job_key} (Triggered by: {triggered_by})")
        except Exception:
            pass

        # Tee stdout/stderr to current_job.log
        tee_out = _StreamTee(sys.stdout)
        tee_err = _StreamTee(sys.stderr)

        with contextlib.redirect_stdout(tee_out), contextlib.redirect_stderr(tee_err):
            try:
                execute_job_target(job_key)
            except Exception as e:
                status = "FAILED"
                error_msg = str(e)
                print(f"\n[JOB ERROR] Exception occurred in job '{job_key}': {e}")
                import traceback
                traceback.print_exc()

        record_job_finish(job_key, status=status, error_msg=error_msg)

        try:
            from logger_setup import get_logger
            logger = get_logger("job_manager")
            logger.audit(f"[AUDIT] Job Finished: {job_key} | Status={status} | Error={error_msg}")
        except Exception:
            pass

    if run_in_background:
        t = threading.Thread(target=_worker, name=f"Job-{job_key}", daemon=True)
        t.start()
        return True
    else:
        _worker()
        return True
