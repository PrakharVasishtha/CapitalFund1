"""
ipo_applied_manager.py
=======================
Manages reading and writing IPO application records to IPO-applied.xlsx.

Header Schema (per user sheet):
  Col 1: IPO-Name
  Col 2: Shares Applied
  Col 3: Issue price
  Col 4: Total Application amount
"""
import os
import sys
import openpyxl

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Base import get_excel_path, parse_float
from common_foundation import log_info, log_error


def get_ipo_applied_path() -> str:
    """Resolves absolute path to IPO-applied.xlsx."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "IPO-applied.xlsx")
    if os.path.exists(path):
        return path
    if os.path.exists("IPO-applied.xlsx"):
        return "IPO-applied.xlsx"
    return path


def fetch_ipo_details_from_general(ipo_name: str, type_ipo: str = "mb") -> tuple[int, float, float]:
    """
    Fetches Shares Applied, Issue Price, and Total Application Amount for an IPO from General.xlsx.
    """
    gen_path = get_excel_path()
    shares_applied = 1
    issue_price = 0.0

    if not os.path.exists(gen_path):
        return shares_applied, issue_price, 0.0

    try:
        wb = openpyxl.load_workbook(gen_path, data_only=True)
        sheets_to_check = ["IPOMB", "IPOSME"] if type_ipo.lower() in ["mb", "mainboard"] else ["IPOSME", "IPOMB"]

        for sheet_name in sheets_to_check:
            if sheet_name not in wb.sheetnames:
                continue

            ws = wb[sheet_name]
            # Discover header indices
            col_price = 45  # Default Column AS (Issue price)
            for c in range(1, min(ws.max_column + 1, 60)):
                val_c = str(ws.cell(1, c).value or "").strip().lower()
                if val_c == "issue price":
                    col_price = c
                    break

            for r in range(2, ws.max_row + 1):
                name_val = str(ws.cell(r, 2).value or "").strip()
                if not name_val:
                    continue

                if ipo_name.lower() in name_val.lower() or name_val.lower() in ipo_name.lower():
                    p_val = ws.cell(r, col_price).value or 0.0
                    try:
                        issue_price = abs(parse_float(str(p_val)))
                    except Exception:
                        issue_price = 0.0

                    # Calculate typical lot shares based on category
                    if issue_price > 0:
                        if type_ipo.lower() in ["sme", "iposme"]:
                            # SME standard lot: ~Rs 1,00,000 - 1,40,000
                            shares_applied = max(1, round(120000 / issue_price))
                        else:
                            # Mainboard standard retail lot: ~Rs 14,000 - 15,000
                            shares_applied = max(1, round(14800 / issue_price))
                    break

            if issue_price > 0:
                break

        wb.close()
    except Exception as e:
        log_error(f"Error reading General.xlsx for {ipo_name}: {e}", exc=e, function_name="fetch_ipo_details_from_general")

    total_amount = round(shares_applied * issue_price, 2)
    return shares_applied, issue_price, total_amount


def record_ipo_application(
    uci: str,
    ipo_name: str,
    type_ipo: str = "mb",
    status: str = "APPLIED",
    failure_reason: str = None
) -> bool:
    """
    Records an IPO application entry into IPO-applied.xlsx under the specified user UCI sheet
    and synchronizes with SQLite ipo_applied table.
    """
    path = get_ipo_applied_path()
    shares_applied, issue_price, total_amount = fetch_ipo_details_from_general(ipo_name, type_ipo)

    try:
        if os.path.exists(path):
            wb = openpyxl.load_workbook(path)
        else:
            wb = openpyxl.Workbook()
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

        raw_uci = str(uci).strip()
        sheet_name = raw_uci.replace("user", "").replace("User", "").strip() if raw_uci.lower().startswith("user") else raw_uci

        if raw_uci in wb.sheetnames:
            sheet_name = raw_uci

        header = ["IPO-Name", "Shares Applied", "Issue price", "Total Application amount", "Status", "Failure Reason"]

        if sheet_name not in wb.sheetnames:
            ws = wb.create_sheet(title=sheet_name)
            ws.append(header)
        else:
            ws = wb[sheet_name]
            # Verify / ensure header
            if ws.max_row == 0 or ws.cell(1, 1).value != "IPO-Name":
                for col_idx, col_name in enumerate(header, start=1):
                    ws.cell(1, col_idx, col_name)

        # Check if entry already exists
        entry_row = None
        for r in range(2, ws.max_row + 1):
            cell_val = str(ws.cell(r, 1).value or "").strip()
            if cell_val.lower() == ipo_name.strip().lower():
                entry_row = r
                break

        status_str = status or "APPLIED"
        fail_str = str(failure_reason) if failure_reason else ""

        if entry_row:
            ws.cell(entry_row, 2, shares_applied)
            ws.cell(entry_row, 3, issue_price)
            ws.cell(entry_row, 4, total_amount)
            ws.cell(entry_row, 5, status_str)
            ws.cell(entry_row, 6, fail_str)
            log_info(f"Updated application entry for '{ipo_name}' in sheet '{sheet_name}' (Row {entry_row}, Status: {status_str})", "record_ipo_application")
        else:
            new_row = ws.max_row + 1
            ws.cell(new_row, 1, ipo_name.strip())
            ws.cell(new_row, 2, shares_applied)
            ws.cell(new_row, 3, issue_price)
            ws.cell(new_row, 4, total_amount)
            ws.cell(new_row, 5, status_str)
            ws.cell(new_row, 6, fail_str)
            log_info(f"Appended application entry for '{ipo_name}' in sheet '{sheet_name}' (Row {new_row}, Status: {status_str})", "record_ipo_application")

        wb.save(path)
        wb.close()

        # Dual-Tier SQLite synchronization
        try:
            import database
            database.record_ipo_application(
                uci=sheet_name,
                ipo_name=ipo_name.strip(),
                shares=shares_applied,
                price=issue_price,
                total_amount=total_amount,
                status=status_str,
                failure_reason=failure_reason
            )
        except Exception as db_err:
            log_error(f"Failed to record IPO application to SQLite: {db_err}", exc=db_err, function_name="record_ipo_application")

        return True

    except Exception as e:
        log_error(f"Failed to record IPO application in '{path}': {e}", exc=e, function_name="record_ipo_application")
        return False


if __name__ == "__main__":
    # Test recording
    res = record_ipo_application("test_uci", "Sample Tech IPO", "mb")
    print("Record test result:", res)
