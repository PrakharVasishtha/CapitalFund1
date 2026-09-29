"""
Centralized logging module for CapitalFund1.

Provides structured logging with multiple handlers:
- Console: INFO level
- capitalfund.log: INFO+ with daily rotation, 30-day retention
- errors.log: ERROR+ only
- debug.log: DEBUG+ (inactive by default)
- audit.log: AUDIT level (25) only
"""

import logging
import logging.handlers
import os
from pathlib import Path

# Custom AUDIT level (25 between INFO=20 and WARNING=30)
AUDIT_LEVEL = 25
logging.AUDIT = AUDIT_LEVEL
logging.addLevelName(AUDIT_LEVEL, "AUDIT")


def _audit(self, message, *args, **kws):
    if self.isEnabledFor(AUDIT_LEVEL):
        self._log(AUDIT_LEVEL, message, args, **kws)


logging.Logger.audit = _audit


def setup_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """
    Configure root logger once. Safe to call multiple times.
    
    Args:
        log_dir: Directory for log files
        level: Root logger level
    """
    # Create logs directory if not exists
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Prevent duplicate handlers on multiple calls
    if root_logger.handlers:
        return
    
    # Define formats
    console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 1. Console handler (INFO+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(console_format, datefmt=date_format))
    root_logger.addHandler(console_handler)
    
    # 2. capitalfund.log — daily rotation (30 days) + size guard (10 MB, 5 backups)
    capital_log_path = log_path / "capitalfund.log"
    capital_handler = logging.handlers.TimedRotatingFileHandler(
        capital_log_path, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    capital_handler.setLevel(logging.INFO)
    capital_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))
    root_logger.addHandler(capital_handler)

    # 3. errors.log — size-rotating (5 MB, 3 backups, ERROR+ only)
    errors_log_path = log_path / "errors.log"
    errors_handler = logging.handlers.RotatingFileHandler(
        errors_log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    errors_handler.setLevel(logging.ERROR)
    errors_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))
    root_logger.addHandler(errors_handler)

    # 3b. error.log (Rotating, ERROR+ only, for compatibility — 5 MB, 5 backups)
    error_compat_path = log_path / "error.log"
    error_compat_handler = logging.handlers.RotatingFileHandler(
        error_compat_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    error_compat_handler.setLevel(logging.ERROR)
    error_compat_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))
    root_logger.addHandler(error_compat_handler)

    # 4. debug.log (DEBUG+, inactive by default - don't add to root)
    # Uncomment below to activate debug logging
    # debug_log_path = log_path / "debug.log"
    # debug_handler = logging.FileHandler(debug_log_path, encoding='utf-8')
    # debug_handler.setLevel(logging.DEBUG)
    # debug_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))
    # root_logger.addHandler(debug_handler)

    # 5. audit.log (AUDIT level only — size-rotating 5 MB, 5 backups)
    audit_log_path = log_path / "audit.log"
    audit_handler = logging.handlers.RotatingFileHandler(
        audit_log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    audit_handler.setLevel(AUDIT_LEVEL)
    audit_handler.setFormatter(logging.Formatter(file_format, datefmt=date_format))

    class AuditFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == AUDIT_LEVEL

    audit_handler.addFilter(AuditFilter())
    root_logger.addHandler(audit_handler)



def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Initialize logging when module is imported
setup_logging()