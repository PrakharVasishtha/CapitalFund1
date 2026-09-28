"""
allotment_application_ipo.py
============================
IPO Application Decision & Execution Engine.

DATA SOURCE CONTRACT
--------------------
The apply / do-not-apply decision is ALWAYS read directly from
General.xlsx (IPOSME and IPOMB sheets) — NEVER from the SQLite database.

  Column  Header              Meaning
  ------  ------------------  -------------------------------------------
  40      ClosingDate (40)    Day-of-month when IPO subscription closes
  41      Appy_or_not         Legacy binary apply flag (1 = apply)
  42      Apply_priority      Formula-computed priority (0 = skip, 1/2/3 = apply)

Reading is done via pandas.read_excel() using column headers (not indices)
so the logic is immune to column-order changes.  For formula cells, pandas
reads the last cached value that Excel stored — the same value a human
operator sees when they open the file.
"""

from datetime import date
import pandas as pd

from Base import get_excel_path
from allotment_kotak_ipo_apply import apply_to_ipo_all_users
from logger_setup import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Column name constants (match exact headers in General.xlsx row 1)
# ---------------------------------------------------------------------------
COL_COMPANY   = "Company Name"          # col B (2)
COL_CLOSE_DAY = "ClosingDate (40)"      # col 40
COL_PRIORITY  = "Apply_priority"        # col 42  ← formula =IF(AK...>threshold, ...)
COL_APPLY_ALT = "Appy_or_not"          # col 41  ← fallback if Apply_priority is missing/blank


def _read_apply_priority(row: pd.Series) -> int:
    """
    Returns the apply priority (0, 1, 2, or 3) for a single IPO row.

    Priority comes from 'Apply_priority' (col 42), with a fallback to
    'Appy_or_not' (col 41).  Both are read directly from Excel.
    The database is never consulted.
    """
    val = None
    if COL_PRIORITY in row.index:
        raw = row[COL_PRIORITY]
        if raw is not None and str(raw).strip() not in ("", "nan", "None"):
            try:
                val = int(float(str(raw).strip()))
            except (ValueError, TypeError):
                val = None

    # Fallback: Appy_or_not
    if val is None and COL_APPLY_ALT in row.index:
        raw = row[COL_APPLY_ALT]
        if raw is not None and str(raw).strip() not in ("", "nan", "None"):
            try:
                val = int(float(str(raw).strip()))
            except (ValueError, TypeError):
                val = None

    return val if val is not None else 0


def _read_close_day(row: pd.Series) -> int:
    """Returns the closing day-of-month from Excel. Returns 0 on parse failure."""
    raw = row.get(COL_CLOSE_DAY)
    if raw is None:
        return 0
    try:
        return int(float(str(raw).strip()))
    except (ValueError, TypeError):
        return 0


def IPO_to_apply():
    """
    Scans General.xlsx for IPOs closing today and returns lists grouped by priority.

    DATA SOURCE: General.xlsx (IPOSME + IPOMB sheets) — read-only.
    The SQLite database is NOT consulted for the apply/no-apply decision.

    Returns
    -------
    tuple: (IPO_mb_3, IPO_sme_3, IPO_mb_2, IPO_sme_2, IPO_mb_1, IPO_sme_1)
        Each element is a list of company name strings (truncated to 15 chars).
    """
    logger.info("--------IPO_to_apply: Scanning closing IPOs from Excel-------")

    IPO_sme_1, IPO_sme_2, IPO_sme_3 = [], [], []
    IPO_mb_1,  IPO_mb_2,  IPO_mb_3  = [], [], []

    path = get_excel_path()
    today = date.today().day

    try:
        df_sme = pd.read_excel(path, sheet_name="IPOSME", header=0)
        df_mb  = pd.read_excel(path, sheet_name="IPOMB",  header=0)
    except Exception as exc:
        logger.error(f"IPO_to_apply: Cannot read General.xlsx — {exc}")
        return IPO_mb_3, IPO_sme_3, IPO_mb_2, IPO_sme_2, IPO_mb_1, IPO_sme_1

    def _process_sheet(df: pd.DataFrame, sheet_tag: str, lists_by_prio: dict) -> None:
        """
        Scans the last 9 rows of a sheet for IPOs closing today with apply priority > 0.
        Appends company names (max 15 chars) into the appropriate list.
        """
        if df.empty:
            logger.warning(f"IPO_to_apply: {sheet_tag} sheet is empty.")
            return

        # Work on the last 9 data rows (most recent IPOs)
        recent = df.dropna(subset=[COL_COMPANY]).tail(9)

        for _, row in recent.iterrows():
            company_raw = row.get(COL_COMPANY)
            if not company_raw or str(company_raw).strip().lower() in ("nan", "none", ""):
                continue

            name      = str(company_raw).strip()[:15]
            priority  = _read_apply_priority(row)
            close_day = _read_close_day(row)

            logger.debug(
                f"[{sheet_tag}] {name!r:16s}  priority={priority}  "
                f"close_day={close_day}  today={today}"
            )

            if priority in (1, 2, 3) and close_day == today:
                lists_by_prio[priority].append(name)
                logger.info(
                    f"[{sheet_tag}] {name!r} → Priority {priority}, closes today (day {today}) — QUEUED"
                )
            elif priority in (1, 2, 3):
                logger.info(
                    f"[{sheet_tag}] {name!r} → Priority {priority} but closes on day {close_day}, not today — SKIP"
                )
            else:
                logger.debug(f"[{sheet_tag}] {name!r} → Apply_priority={priority} — SKIP (not applying)")

    _process_sheet(df_sme, "IPOSME", {1: IPO_sme_1, 2: IPO_sme_2, 3: IPO_sme_3})
    _process_sheet(df_mb,  "IPOMB",  {1: IPO_mb_1,  2: IPO_mb_2,  3: IPO_mb_3})

    logger.info(
        f"IPO_to_apply result — "
        f"MB P3={IPO_mb_3}, SME P3={IPO_sme_3}, "
        f"MB P2={IPO_mb_2}, SME P2={IPO_sme_2}, "
        f"MB P1={IPO_mb_1}, SME P1={IPO_sme_1}"
    )
    return IPO_mb_3, IPO_sme_3, IPO_mb_2, IPO_sme_2, IPO_mb_1, IPO_sme_1


def ipo_application():
    """
    Scheduled job: reads the apply decision from Excel and submits IPO applications.

    Execution order: Priority 3 (highest conviction) → Priority 2 → Priority 1.
    Within each priority: Mainboard first, then SME.
    """
    logger.info("-----------ipo_application: Executing scheduled IPO applications----------")
    IPO_mb_3, IPO_sme_3, IPO_mb_2, IPO_sme_2, IPO_mb_1, IPO_sme_1 = IPO_to_apply()

    logger.info(
        f"Applying for IPOs: MB3={IPO_mb_3}, SME3={IPO_sme_3}, "
        f"MB2={IPO_mb_2}, SME2={IPO_sme_2}, MB1={IPO_mb_1}, SME1={IPO_sme_1}"
    )

    for ipo in IPO_mb_3:
        logger.info(f"Processing Priority 3 Mainboard IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="mb")
        except Exception as e:
            logger.exception(f"Error applying to MB3 IPO {ipo}: {e}")

    for ipo in IPO_sme_3:
        logger.info(f"Processing Priority 3 SME IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="sme")
        except Exception as e:
            logger.exception(f"Error applying to SME3 IPO {ipo}: {e}")

    for ipo in IPO_mb_2:
        logger.info(f"Processing Priority 2 Mainboard IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="mb")
        except Exception as e:
            logger.exception(f"Error applying to MB2 IPO {ipo}: {e}")

    for ipo in IPO_sme_2:
        logger.info(f"Processing Priority 2 SME IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="sme")
        except Exception as e:
            logger.exception(f"Error applying to SME2 IPO {ipo}: {e}")

    for ipo in IPO_mb_1:
        logger.info(f"Processing Priority 1 Mainboard IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="mb")
        except Exception as e:
            logger.exception(f"Error applying to MB1 IPO {ipo}: {e}")

    for ipo in IPO_sme_1:
        logger.info(f"Processing Priority 1 SME IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="sme")
        except Exception as e:
            logger.exception(f"Error applying to SME1 IPO {ipo}: {e}")