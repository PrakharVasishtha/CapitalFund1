# Logging System Implementation Task

## Overview
Implement a comprehensive logging system for capitalfund1. Replace scattered print() calls and the old `common_foundation.logger()` with Python's built-in `logging` module.

## FIRST: Sync
```bash
cd D:\CapitalFund1 && git pull origin master
```

---

## PHASE 1: Core Logger Module

### Create `src/logger_setup.py`
- `setup_logging()` — configures root logger once
- `get_logger(name)` — returns a named logger
- Log format: `TIMESTAMP | LEVEL | MODULE | MESSAGE`
- Example: `2026-09-09 14:30:15 | INFO | trader_smws | NIFTYIETF sell order placed`
- Handlers:
  * **Console** (StreamHandler): INFO level, format: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`
  * **capitalfund.log** (TimedRotatingFileHandler): INFO+, daily rotation, 30-day retention, UTF-8
  * **errors.log** (FileHandler): ERROR+ only, UTF-8
  * **debug.log** (FileHandler): DEBUG+ only (include but don't activate by default)
  * **audit.log** (FileHandler): AUDIT level (25) only
- Create `logs/` directory if not exists
- Add custom AUDIT level: `logging.AUDIT = 25` and `logging.addLevelName(25, "AUDIT")`

### Update `src/common_foundation.py`
- Import `logging` and `get_logger` from `logger_setup`
- Replace the `logger()` function body to use Python logging internally:
```python
def logger(file, StringText="OK", FunctionName="In Function"):
    s = FunctionName + " : " + str(StringText) + " at MM-DD HH:MM :" + str(datetime.datetime.now())[5:16]
    # Keep old behavior (write to file) for backward compat
    try:
        f = open(file, "a")
        f.write(s)
        f.write("\n")
        f.close()
    except Exception:
        pass
    # Also log via new system
    _logger = get_logger("common_foundation")
    _logger.info(f"{FunctionName}: {StringText}")
    print(s)
    time.sleep(1)
```

### Update `src/common_schedule_all.py`
- Add `from logger_setup import setup_logging` at top
- Call `setup_logging()` at module load
- Add `logger = get_logger(__name__)` at top
- Replace exception handlers: `common_foundation.logger("system.txt", Argument, "name")` → `logger.exception("Problem in name")`

### Commit: "feat: add centralized logging module with structured log levels"

---

## PHASE 2: Module Migration

For each module in `src/`, add at the top:
```python
from logger_setup import get_logger
logger = get_logger(__name__)
```

### Migration Rules:
| Current Pattern | New Pattern |
|----------------|-------------|
| `print("status message")` | `logger.info("status message")` |
| `print(f"Error: {e}")` | `logger.error(f"Error: {e}")` |
| `except Exception as e: print(e)` | `except Exception as e: logger.exception("descriptive message")` |
| `except Exception as e: ... import traceback` | `except Exception as e: logger.exception("descriptive message")` (remove traceback import) |
| `except: print(...)` | `except Exception: logger.exception("descriptive message")` |

### Files to migrate (one batch):
- `src/trader_zerodha_sell.py`
- `src/trader_zerodha_buy.py`
- `src/trader_smws.py`
- `src/trader_priority_ipo_smws_sell.py`
- `src/allotment_application_ipo.py`
- `src/allotment_kotak_ipo_apply.py`
- `src/allotment_fetch.py`
- `src/allotment_general.py`
- `src/allotment_update.py`
- `src/fund_manager.py`
- `src/fund_zerodha_withdraw.py`
- `src/fund_bank_to_kite.py`
- `src/fund_kotak_get_balance.py`
- `src/fund_transfer_for_smws.py`
- `src/ipo_scraper.py`
- `src/ipo_excel_manager.py`
- `src/ipo_excel_3pm.py`
- `src/ipo_ExtractGMP.py`
- `src/ipo_ExtractSubscription.py`
- `src/common_master_functions.py`
- `src/special_sesion_zerodha_sell.py`
- `src/special_session_monitor.py`
- `src/special_session_indicative_price_bse.py`
- `src/special_session_indicative_price_nse.py`

### Rules:
- Do NOT change any business logic
- Do NOT change function signatures
- Keep all existing behavior intact
- Keep `dprint()` as-is (debug toggle)
- Each file must still work with the old `from common_foundation import *` pattern

### Commit: "feat: migrate all modules to structured logging"

---

## PHASE 3: Audit Logging

Add audit-level logging for critical operations:

### In `src/trader_zerodha_buy.py`:
```python
logger.log(25, f"AUDIT: Buy order placed | User: {user_id} | Symbol: {security_symbol} | Qty: {quantity} | Price: {price}")
```

### In `src/trader_zerodha_sell.py`:
```python
logger.log(25, f"AUDIT: Sell order placed | User: {user_id} | Symbol: {security_symbol}")
```

### In `src/allotment_kotak_ipo_apply.py`:
```python
logger.log(25, f"AUDIT: IPO applied | IPO: {ipo_name} | Category: {type_ipo}")
```

### In `src/fund_zerodha_withdraw.py`:
```python
logger.log(25, f"AUDIT: Fund withdrawal | Amount: {amount} | Status: success")
```

### In `src/fund_transfer_for_smws.py`:
```python
logger.log(25, f"AUDIT: Fund transfer to Kite | Amount: {final_amount}")
```

### Commit: "feat: add audit logging for trades, IPO applications, and fund transfers"

---

## PHASE 4: Cleanup

- Remove commented-out print statements (lines starting with `#print`)
- Remove unused `import traceback` where replaced by `logger.exception()`
- Ensure no bare `except:` blocks remain (all should be `except Exception:`)
- Verify `logs/*.log` is in `.gitignore`

### Commit: "chore: cleanup old debug prints and bare except blocks"

---

## Verification
After all phases, run from `D:\CapitalFund1`:
```bash
python -c "from common_schedule_all import *; print('Import OK')"
```

Then show:
```bash
git log --oneline -6
```

## CRITICAL RULES
1. **Do NOT change business logic** — only logging
2. **Do NOT change function signatures**
3. **Keep backward compatibility** — old `logger(file, text, func)` calls must still work
4. **One commit per phase**
5. **UTF-8 encoding** on all file handlers
