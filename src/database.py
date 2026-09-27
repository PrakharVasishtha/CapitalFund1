"""
database.py
===========
Dual-Tier Data Storage Engine for CapitalFund1.

Provides a robust, non-blocking SQLite database backend (capitalfund.db) with
Write-Ahead Logging (WAL) mode for concurrency, paired with automatic bidirectional
synchronization to the existing Excel spreadsheets:
  - Master.xlsx         <--> master_users table
  - allotted_holdings.xlsx <--> allotted_holdings table
  - General.xlsx        <--> ipo_research table
  - IPO-applied.xlsx    <--> ipo_applied table

This eliminates file-locking errors (PermissionError when Excel is open in MS Excel/viewers),
speeds up transactional queries across the automation loop, and preserves full Excel
visibility for human operators.
"""

import os
import sys
import sqlite3
import openpyxl
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Base import (
    safe_load_workbook,
    safe_save_workbook,
    parse_float,
    get_excel_path,
    load_credentials,
)
from common_foundation import log_info, log_error, log_warning


def get_db_path() -> str:
    """Returns absolute path to SQLite database file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "capitalfund.db")


def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to SQLite with WAL mode and row factory enabled.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Initializes database schema and indexes if they do not exist.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. master_users table (syncs with Master.xlsx 'Users')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_users (
                uci TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                mobile TEXT,
                communication_email TEXT,
                account_email TEXT,
                intraday INTEGER DEFAULT 0,
                zerodha_access_token TEXT,
                current_value REAL DEFAULT 0.0,
                bank_balance REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. allotted_holdings table (syncs with allotted_holdings.xlsx)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS allotted_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uci TEXT NOT NULL,
                security_name TEXT NOT NULL,
                lot_size INTEGER DEFAULT 1,
                issue_price REAL DEFAULT 0.0,
                shares_allocated INTEGER DEFAULT 0,
                lots_issued INTEGER DEFAULT 0,
                exchange TEXT DEFAULT 'NSE',
                stock_category TEXT DEFAULT 'Mainboard',
                special_session_status INTEGER DEFAULT 0,
                regular_session_status INTEGER DEFAULT 0,
                listing_date TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(uci, security_name)
            );
        """)

        # 3. ipo_research table (syncs with General.xlsx 'IPOMB' and 'IPOSME')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ipo_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                company_name TEXT NOT NULL,
                category TEXT NOT NULL,  -- 'MB' or 'SME'
                listing_result INTEGER DEFAULT 0,
                total_score REAL DEFAULT 0.0,
                gmp REAL DEFAULT 0.0,
                gmp_percent REAL DEFAULT 0.0,
                retail_subscription REAL DEFAULT 0.0,
                qib_subscription REAL DEFAULT 0.0,
                nii_subscription REAL DEFAULT 0.0,
                pe_ratio REAL DEFAULT 0.0,
                closing_date INTEGER,
                apply_priority INTEGER DEFAULT 0,
                issue_price REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. ipo_applied table (syncs with IPO-applied.xlsx)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ipo_applied (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uci TEXT NOT NULL,
                ipo_name TEXT NOT NULL,
                shares_applied INTEGER DEFAULT 1,
                issue_price REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                applied_date TEXT,
                status TEXT DEFAULT 'APPLIED',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(uci, ipo_name)
            );
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_uci ON allotted_holdings(uci);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_statuses ON allotted_holdings(special_session_status, regular_session_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_category ON ipo_research(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applied_uci ON ipo_applied(uci);")

        conn.commit()
        log_info("SQLite database schema initialized successfully (WAL mode enabled).", "init_db")
    except Exception as e:
        log_error(f"Error initializing SQLite database: {e}", exc=e, function_name="init_db")
    finally:
        conn.close()


# ==============================================================================
# Ingestion: Import from Excel into SQLite
# ==============================================================================

def import_master_from_excel():
    """Imports Master.xlsx into SQLite master_users table."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    master_path = os.path.join(base_dir, "Master.xlsx")
    if not os.path.exists(master_path):
        return

    conn = get_connection()
    try:
        wb = safe_load_workbook(master_path, data_only=True)
        if "Users" not in wb.sheetnames:
            wb.close()
            return
        ws = wb["Users"]
        cursor = conn.cursor()

        for r in range(2, ws.max_row + 1):
            uci_val = ws.cell(r, 1).value
            if uci_val is None:
                continue
            uci = str(uci_val).replace("user", "").strip()
            first_name = str(ws.cell(r, 2).value or "").strip()
            last_name = str(ws.cell(r, 3).value or "").strip()
            mobile = str(ws.cell(r, 4).value or "").strip()
            comm_email = str(ws.cell(r, 5).value or "").strip()
            acc_email = str(ws.cell(r, 6).value or "").strip()
            intraday = int(ws.cell(r, 7).value or 0)
            token = str(ws.cell(r, 8).value or "").strip()
            val = parse_float(ws.cell(r, 9).value or 0.0)

            cursor.execute("""
                INSERT INTO master_users (
                    uci, first_name, last_name, mobile, communication_email,
                    account_email, intraday, zerodha_access_token, current_value, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(uci) DO UPDATE SET
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    mobile=excluded.mobile,
                    communication_email=excluded.communication_email,
                    account_email=excluded.account_email,
                    intraday=excluded.intraday,
                    zerodha_access_token=excluded.zerodha_access_token,
                    current_value=excluded.current_value,
                    updated_at=CURRENT_TIMESTAMP;
            """, (uci, first_name, last_name, mobile, comm_email, acc_email, intraday, token, val))

        conn.commit()
        wb.close()
    except Exception as e:
        log_error(f"Error importing Master.xlsx into SQLite: {e}", exc=e, function_name="import_master_from_excel")
    finally:
        conn.close()


def import_allotted_holdings_from_excel():
    """Imports allotted_holdings.xlsx into SQLite allotted_holdings table."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "allotted_holdings.xlsx")
    if not os.path.exists(path):
        return

    conn = get_connection()
    try:
        wb = safe_load_workbook(path, data_only=True)
        cursor = conn.cursor()

        for sheet_name in wb.sheetnames:
            clean_uci = sheet_name.replace("user", "").strip()
            ws = wb[sheet_name]

            for r in range(2, ws.max_row + 1):
                sym = ws.cell(r, 1).value
                if not sym or str(sym).strip().lower() in ["none", ""]:
                    continue
                security_name = str(sym).strip()
                lot_size = int(ws.cell(r, 2).value or 1)
                issue_price = parse_float(ws.cell(r, 3).value or 0.0)
                shares_allocated = int(ws.cell(r, 4).value or 0)
                lots_issued = int(ws.cell(r, 5).value or 0) if isinstance(ws.cell(r, 5).value, (int, float)) else 0
                exchange = str(ws.cell(r, 6).value or "NSE").strip().upper()
                category = str(ws.cell(r, 7).value or "Mainboard").strip()

                # Status columns
                spl_status = 0
                try:
                    spl_status = int(ws.cell(r, 8).value or 0)
                except Exception:
                    pass

                reg_status = 0
                try:
                    reg_status = int(ws.cell(r, 11).value or 0)
                except Exception:
                    pass

                cursor.execute("""
                    INSERT INTO allotted_holdings (
                        uci, security_name, lot_size, issue_price, shares_allocated,
                        lots_issued, exchange, stock_category, special_session_status,
                        regular_session_status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(uci, security_name) DO UPDATE SET
                        lot_size=excluded.lot_size,
                        issue_price=excluded.issue_price,
                        shares_allocated=excluded.shares_allocated,
                        lots_issued=excluded.lots_issued,
                        exchange=excluded.exchange,
                        stock_category=excluded.stock_category,
                        special_session_status=excluded.special_session_status,
                        regular_session_status=excluded.regular_session_status,
                        updated_at=CURRENT_TIMESTAMP;
                """, (clean_uci, security_name, lot_size, issue_price, shares_allocated, lots_issued, exchange, category, spl_status, reg_status))

        conn.commit()
        wb.close()
    except Exception as e:
        log_error(f"Error importing allotted_holdings.xlsx into SQLite: {e}", exc=e, function_name="import_allotted_holdings_from_excel")
    finally:
        conn.close()


def import_general_from_excel():
    """Imports General.xlsx ('IPOMB' and 'IPOSME') into SQLite ipo_research table."""
    path = get_excel_path("General.xlsx")
    if not os.path.exists(path):
        return

    conn = get_connection()
    try:
        wb = safe_load_workbook(path, data_only=True)
        cursor = conn.cursor()

        for sheet_name, cat in [("IPOMB", "MB"), ("IPOSME", "SME")]:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            for r in range(2, ws.max_row + 1):
                url = str(ws.cell(r, 1).value or "").strip()
                name = str(ws.cell(r, 2).value or "").strip()
                if not name and not url:
                    continue
                if not url:
                    url = f"local://{cat}/{name}"

                res_val = int(ws.cell(r, 4).value or 0) if isinstance(ws.cell(r, 4).value, (int, float)) else 0
                score = parse_float(ws.cell(r, 5).value or 0.0)
                gmp = parse_float(ws.cell(r, 7).value or 0.0)
                gmp_pct = parse_float(ws.cell(r, 8).value or 0.0)
                retail_sub = parse_float(ws.cell(r, 11).value or 0.0)
                qib_sub = parse_float(ws.cell(r, 12).value or 0.0)
                nii_sub = parse_float(ws.cell(r, 13).value or 0.0)
                pe = parse_float(ws.cell(r, 20).value or 0.0)
                close_dt = int(ws.cell(r, 40).value or 0) if isinstance(ws.cell(r, 40).value, (int, float)) else None
                priority = int(ws.cell(r, 42).value or 0) if isinstance(ws.cell(r, 42).value, (int, float)) else 0
                price = parse_float(ws.cell(r, 45).value or 0.0)

                cursor.execute("""
                    INSERT INTO ipo_research (
                        url, company_name, category, listing_result, total_score,
                        gmp, gmp_percent, retail_subscription, qib_subscription,
                        nii_subscription, pe_ratio, closing_date, apply_priority,
                        issue_price, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(url) DO UPDATE SET
                        company_name=excluded.company_name,
                        category=excluded.category,
                        listing_result=excluded.listing_result,
                        total_score=excluded.total_score,
                        gmp=excluded.gmp,
                        gmp_percent=excluded.gmp_percent,
                        retail_subscription=excluded.retail_subscription,
                        qib_subscription=excluded.qib_subscription,
                        nii_subscription=excluded.nii_subscription,
                        pe_ratio=excluded.pe_ratio,
                        closing_date=excluded.closing_date,
                        apply_priority=excluded.apply_priority,
                        issue_price=excluded.issue_price,
                        updated_at=CURRENT_TIMESTAMP;
                """, (url, name, cat, res_val, score, gmp, gmp_pct, retail_sub, qib_sub, nii_sub, pe, close_dt, priority, price))

        conn.commit()
        wb.close()
    except Exception as e:
        log_error(f"Error importing General.xlsx into SQLite: {e}", exc=e, function_name="import_general_from_excel")
    finally:
        conn.close()


def import_applied_from_excel():
    """Imports IPO-applied.xlsx into SQLite ipo_applied table."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "IPO-applied.xlsx")
    if not os.path.exists(path):
        return

    conn = get_connection()
    try:
        wb = safe_load_workbook(path, data_only=True)
        cursor = conn.cursor()

        for sheet_name in wb.sheetnames:
            clean_uci = sheet_name.replace("user", "").strip()
            ws = wb[sheet_name]
            for r in range(2, ws.max_row + 1):
                name_val = ws.cell(r, 1).value
                if not name_val:
                    continue
                ipo_name = str(name_val).strip()
                shares = int(ws.cell(r, 2).value or 1)
                price = parse_float(ws.cell(r, 3).value or 0.0)
                amt = parse_float(ws.cell(r, 4).value or 0.0)

                cursor.execute("""
                    INSERT INTO ipo_applied (
                        uci, ipo_name, shares_applied, issue_price, total_amount, updated_at
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(uci, ipo_name) DO UPDATE SET
                        shares_applied=excluded.shares_applied,
                        issue_price=excluded.issue_price,
                        total_amount=excluded.total_amount,
                        updated_at=CURRENT_TIMESTAMP;
                """, (clean_uci, ipo_name, shares, price, amt))

        conn.commit()
        wb.close()
    except Exception as e:
        log_error(f"Error importing IPO-applied.xlsx into SQLite: {e}", exc=e, function_name="import_applied_from_excel")
    finally:
        conn.close()


def import_all_from_excel():
    """Imports data from all 4 primary Excel files into SQLite."""
    init_db()
    import_master_from_excel()
    import_allotted_holdings_from_excel()
    import_general_from_excel()
    import_applied_from_excel()
    log_info("Completed full Excel -> SQLite synchronization.", "import_all_from_excel")


# ==============================================================================
# Export: Sync SQLite State Back into Excel
# ==============================================================================

def sync_master_to_excel():
    """Exports SQLite master_users back to Master.xlsx."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "Master.xlsx")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM master_users ORDER BY CAST(uci AS INTEGER);")
        rows = cursor.fetchall()
        if not rows:
            return

        if os.path.exists(path):
            wb = safe_load_workbook(path)
        else:
            wb = openpyxl.Workbook()

        if "Users" not in wb.sheetnames:
            ws = wb.create_sheet("Users", 0)
        else:
            ws = wb["Users"]

        headers = [
            "uci", "first_name", "last_name", "mobile",
            "communication email", "account_email", "intraday",
            "zerodha_access_token", "current_value"
        ]
        for col_idx, h in enumerate(headers, 1):
            ws.cell(1, col_idx, h)

        for r_idx, row in enumerate(rows, 2):
            ws.cell(r_idx, 1, row["uci"])
            ws.cell(r_idx, 2, row["first_name"])
            ws.cell(r_idx, 3, row["last_name"])
            ws.cell(r_idx, 4, row["mobile"])
            ws.cell(r_idx, 5, row["communication_email"])
            ws.cell(r_idx, 6, row["account_email"])
            ws.cell(r_idx, 7, row["intraday"])
            ws.cell(r_idx, 8, row["zerodha_access_token"])
            ws.cell(r_idx, 9, row["current_value"])

        safe_save_workbook(wb, path)
        wb.close()
    except Exception as e:
        log_error(f"Error syncing SQLite to Master.xlsx: {e}", exc=e, function_name="sync_master_to_excel")
    finally:
        conn.close()


def sync_allotted_holdings_to_excel():
    """Exports SQLite allotted_holdings back to allotted_holdings.xlsx."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "allotted_holdings.xlsx")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT uci FROM allotted_holdings;")
        ucis = [r["uci"] for r in cursor.fetchall()]
        if not ucis:
            return

        if os.path.exists(path):
            wb = safe_load_workbook(path)
        else:
            wb = openpyxl.Workbook()

        headers = [
            "security_name", "lot_size", "issue_price", "shares_allocated",
            "lots_issued", "exchange", "stock_category", "special_session_status",
            "order_id", "reserved", "regular_session_status"
        ]

        for uci in ucis:
            sheet_name = str(uci)
            if sheet_name not in wb.sheetnames:
                ws = wb.create_sheet(sheet_name)
            else:
                ws = wb[sheet_name]

            # Write header
            for col_idx, h in enumerate(headers, 1):
                ws.cell(1, col_idx, h)

            cursor.execute("SELECT * FROM allotted_holdings WHERE uci = ? ORDER BY id;", (uci,))
            records = cursor.fetchall()
            for r_idx, rec in enumerate(records, 2):
                ws.cell(r_idx, 1, rec["security_name"])
                ws.cell(r_idx, 2, rec["lot_size"])
                ws.cell(r_idx, 3, rec["issue_price"])
                ws.cell(r_idx, 4, rec["shares_allocated"])
                ws.cell(r_idx, 5, rec["lots_issued"])
                ws.cell(r_idx, 6, rec["exchange"])
                ws.cell(r_idx, 7, rec["stock_category"])
                ws.cell(r_idx, 8, rec["special_session_status"])
                ws.cell(r_idx, 11, rec["regular_session_status"])

        safe_save_workbook(wb, path)
        wb.close()
    except Exception as e:
        log_error(f"Error syncing SQLite to allotted_holdings.xlsx: {e}", exc=e, function_name="sync_allotted_holdings_to_excel")
    finally:
        conn.close()


def sync_all_to_excel():
    """Synchronizes all SQLite tables to their respective Excel files."""
    sync_master_to_excel()
    sync_allotted_holdings_to_excel()
    log_info("Exported SQLite tables cleanly to Excel spreadsheets.", "sync_all_to_excel")


# ==============================================================================
# Fast CRUD Helper Methods for Application Modules
# ==============================================================================

def get_allotted_holdings(
    uci: Optional[str] = None,
    special_session_status: Optional[int] = None,
    regular_session_status: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves allotted holdings matching optional filters without Excel I/O overhead.
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM allotted_holdings WHERE 1=1"
        params: List[Any] = []
        if uci is not None:
            query += " AND uci = ?"
            params.append(str(uci).replace("user", "").strip())
        if special_session_status is not None:
            query += " AND special_session_status = ?"
            params.append(special_session_status)
        if regular_session_status is not None:
            query += " AND regular_session_status = ?"
            params.append(regular_session_status)

        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_holding_status(
    uci: str,
    security_name: str,
    special_session_status: Optional[int] = None,
    regular_session_status: Optional[int] = None,
    auto_sync_excel: bool = True,
):
    """
    Updates listing session lifecycle status for a holding and syncs to Excel.
    """
    conn = get_connection()
    clean_uci = str(uci).replace("user", "").strip()
    try:
        cursor = conn.cursor()
        if special_session_status is not None and regular_session_status is not None:
            cursor.execute("""
                UPDATE allotted_holdings
                SET special_session_status = ?, regular_session_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE uci = ? AND security_name = ?;
            """, (special_session_status, regular_session_status, clean_uci, security_name))
        elif special_session_status is not None:
            cursor.execute("""
                UPDATE allotted_holdings
                SET special_session_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE uci = ? AND security_name = ?;
            """, (special_session_status, clean_uci, security_name))
        elif regular_session_status is not None:
            cursor.execute("""
                UPDATE allotted_holdings
                SET regular_session_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE uci = ? AND security_name = ?;
            """, (regular_session_status, clean_uci, security_name))
        conn.commit()
    finally:
        conn.close()

    if auto_sync_excel:
        sync_allotted_holdings_to_excel()


def record_ipo_application(
    uci: str,
    ipo_name: str,
    shares: int,
    price: float,
    total_amount: float,
    applied_date: Optional[str] = None,
):
    """
    Records an IPO application in SQLite and updates the dual-tier layer.
    """
    conn = get_connection()
    clean_uci = str(uci).replace("user", "").strip()
    dt = applied_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ipo_applied (
                uci, ipo_name, shares_applied, issue_price, total_amount, applied_date, status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'APPLIED', CURRENT_TIMESTAMP)
            ON CONFLICT(uci, ipo_name) DO UPDATE SET
                shares_applied = excluded.shares_applied,
                issue_price = excluded.issue_price,
                total_amount = excluded.total_amount,
                applied_date = excluded.applied_date,
                updated_at = CURRENT_TIMESTAMP;
        """, (clean_uci, ipo_name, shares, price, total_amount, dt))
        conn.commit()
    finally:
        conn.close()


def update_user_valuation(uci: str, current_value: float, auto_sync_excel: bool = True):
    """
    Updates the portfolio valuation for a user account in SQLite.
    """
    conn = get_connection()
    clean_uci = str(uci).replace("user", "").strip()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE master_users
            SET current_value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE uci = ?;
        """, (current_value, clean_uci))
        conn.commit()
    finally:
        conn.close()

    if auto_sync_excel:
        sync_master_to_excel()
