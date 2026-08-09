import os
import datetime
import time
import smtplib, ssl
import json
import logging
from logging.handlers import RotatingFileHandler
import traceback
from email.message import EmailMessage
import urllib.request
from urllib.request import urlopen
from dotenv import load_dotenv


load_dotenv()

# ── Centralized Logging Setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
ERROR_LOG_PATH = os.path.join(LOG_DIR, "error.log")

app_logger = logging.getLogger("CapitalFund1")
app_logger.setLevel(logging.INFO)

if not app_logger.handlers:
    # Rotating file handler (5 MB per log file, max 5 backup logs)
    file_handler = RotatingFileHandler(ERROR_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d:%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    app_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    app_logger.addHandler(console_handler)


def log_error(msg: str, exc: Exception = None, function_name: str = ""):
    """
    Logs an error message along with full exception traceback to logs/error.log and console.
    """
    prefix = f"[{function_name}] " if function_name else ""
    full_msg = f"{prefix}{msg}"
    if exc:
        app_logger.error(f"{full_msg} | Exception: {exc}\n{traceback.format_exc()}")
    else:
        app_logger.error(full_msg)


def log_info(msg: str, function_name: str = ""):
    """
    Logs an informational message to logs/error.log and console.
    """
    prefix = f"[{function_name}] " if function_name else ""
    app_logger.info(f"{prefix}{msg}")


def logger(file="system.txt", StringText="OK", FunctionName="In Function"):
    """
    Legacy logging function kept for backwards compatibility.
    Appends to specified txt file and forwards log entry to central app_logger.
    """
    s = f"{FunctionName} : {StringText} at MM-DD HH:MM :{datetime.datetime.now():%m-%d %H:%M}"
    try:
        f = open(file, "a", encoding="utf-8")
        f.write(s + "\n")
        f.close()
    except Exception:
        pass
    app_logger.info(s)
    time.sleep(0.1)


def dprint(a=".", b=" ", c=" ", d=" ", e=" ", f=" ", g=" ", h=" "):
    i = 0
    if i == 1:
        print(f"{a} {b} {c} {d} {e} {f} {g} {h}")


def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1


def timenow():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time


def send_email(email_to="prakharvasishtha9@gmail.com", sub_send="default", content_send="default"):
    email_address = os.getenv("ALERT_EMAIL_USER", "vasistcapital@gmail.com")
    email_password = os.getenv("ALERT_EMAIL_PASS", "nbfdhxifzaekznjg")

    msg = EmailMessage()
    msg['Subject'] = sub_send
    msg['From'] = email_address
    msg['To'] = email_to
    msg.set_content(content_send)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        log_info(f"Email sent successfully to {email_to} (Subject: {sub_send})", "send_email")
    except Exception as e:
        log_error(f"SMTP 587 failed: {e}", exc=e, function_name="send_email")
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_address, email_password)
                smtp.send_message(msg)
            log_info(f"Email sent successfully via SSL to {email_to}", "send_email")
        except Exception as ssl_err:
            log_error(f"SMTP_SSL 465 failed: {ssl_err}", exc=ssl_err, function_name="send_email")
            logger("system.txt", sub_send, "send_email")


def send_email_with_excel(mail_subject="default", mail_content="default", path_of_file="default", email_to="prakharvasishtha9@gmail.com"):
    email_address = os.getenv("ALERT_EMAIL_USER", "vasistcapital@gmail.com")
    email_password = os.getenv("ALERT_EMAIL_PASS", "nbfdhxifzaekznjg")

    msg = EmailMessage()
    msg['Subject'] = mail_subject
    msg['From'] = email_address
    msg['To'] = email_to
    msg.set_content(mail_content)

    file_path = os.path.abspath(path_of_file) if os.path.exists(path_of_file) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', path_of_file))
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)

        msg.add_attachment(
            file_data,
            maintype='application',
            subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=file_name
        )
    except FileNotFoundError as fnf_err:
        log_error(f"Excel attachment file not found at '{file_path}'", exc=fnf_err, function_name="send_email_with_excel")
        return

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        log_info(f"Email sent successfully with attachment '{file_name}' to {email_to}", "send_email_with_excel")
    except Exception as e:
        log_error(f"Email sending with excel attachment failed: {e}", exc=e, function_name="send_email_with_excel")
        logger("system.txt", "send_email_with_excel", "send_email_with_excel")


def internet_on(a1="nosub"):
    try:
        urlopen('http://www.google.com/', timeout=1)
        return True
    except Exception as e:
        log_error(f"Internet connection check failed: {e}", function_name="internet_on")
        return False


def internetcheck(b="NoSubject"):
    while not (internet_on(b)):
        log_error("Internet offline. Waiting 20s before retrying...", function_name="internetcheck")
        logger("LogInternet.txt", "Offline", "internet")
        time.sleep(20)


def send_telegram_notification(msg: str, parse_mode: str = "HTML") -> bool:
    """
    Sends a push notification via Telegram Bot API.
    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables (.env).
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        log_info("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.", "send_telegram_notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                log_info("Telegram notification sent successfully.", "send_telegram_notification")
                return True
    except Exception as e:
        log_error(f"Failed to send Telegram notification: {e}", exc=e, function_name="send_telegram_notification")

    return False

