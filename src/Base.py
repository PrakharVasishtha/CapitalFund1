from cleanfetcheddata import clean_ipo_data
from IpoDataExtractor import ChittorgarhIPOExtractor, IPOData
import openpyxl
import imaplib
import email
from email import message_from_bytes
import re
import time
import datetime
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from typing import Dict, Any
import yfinance as yf

def get_vix():
    try:
        vix_value = yf.Ticker("^INDIAVIX").info.get('regularMarketPrice')
        #print("Current India VIX:", round(vix_value, 2) if vix_value else "N/A")
    except:
        vix_value = 13.5
    return vix_value


def parse_float(val: Any) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return 0.0
    val = val.replace('%', '').replace('x', '').replace(',', '').replace('₹', '').replace('Cr', '').strip()
    try:
        return float(val)
    except ValueError:
        return 0.0

def get_netbanking_otp(EMAIL_USER,EMAIL_PASS, search_query, retries=15, delay=4):
    for i in range(retries):
        print(f"Attempt {i + 1}: Searching for OTP...")
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")

            # Search for the specific subject and ensure it's unread
            status, messages = mail.search(None, search_query)
            print(status, messages)
            if status == "OK" and messages[0]:
                # Get the list of matching message IDs and iterate backwards from the latest
                message_ids = messages[0].split()
                print(message_ids)
                for latest_id in reversed(message_ids):
                    _, msg_data = mail.fetch(latest_id, "(RFC822)")
                    msg = message_from_bytes(msg_data[0][1])

                    # --- NEW TIME FILTERING CODE ---
                    # Parse the 'Date' header to a datetime object
                    email_date = parsedate_to_datetime(msg.get("Date"))
                    now = datetime.datetime.now(datetime.timezone.utc)

                    # Calculate the difference in minutes
                    time_diff = (now - email_date).total_seconds() / 60

                    # If the email is older than 2 minutes, skip it
                    if time_diff > 2:
                        continue
                        # -------------------------------

                    body = ""
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type in ["text/html", "text/plain"]:
                            payload = part.get_payload(decode=True).decode(errors='ignore')
                            body += payload

                    clean_body = re.sub(r'<[^>]+>', ' ', body)
                    otp_match = re.search(r'is\s+(\d{6})', clean_body, re.IGNORECASE)

                    if otp_match:
                        print("otp found")
                        mail.store(latest_id, '+FLAGS', '\\Seen')
                        mail.logout()
                        return otp_match.group(1)

            mail.logout()
        except Exception as e:
            print(f"Error: {str(e)}")

        time.sleep(delay)
    return None


def otp_shoonya(EMAIL_USER,EMAIL_PASS, search_query, retries=15, delay=7):
    for i in range(retries):
        print(f"Attempt {i + 1}: Searching for OTP...")
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")

            # Search for the specific subject and ensure it's unread
            status, messages = mail.search(None, search_query)

            if status == "OK" and messages[0]:
                # Get the list of matching message IDs and iterate backwards from the latest
                message_ids = messages[0].split()
                for latest_id in reversed(message_ids):
                    _, msg_data = mail.fetch(latest_id, "(RFC822)")
                    msg = message_from_bytes(msg_data[0][1])

                    # --- NEW TIME FILTERING CODE ---
                    # Parse the 'Date' header to a datetime object
                    email_date = parsedate_to_datetime(msg.get("Date"))
                    now = datetime.datetime.now(datetime.timezone.utc)

                    # Calculate the difference in minutes
                    time_diff = (now - email_date).total_seconds() / 60

                    # If the email is older than 2 minutes, skip it
                    if time_diff > 2:
                        continue
                        # -------------------------------

                    body = ""
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type in ["text/html", "text/plain"]:
                            payload = part.get_payload(decode=True).decode(errors='ignore')
                            body += payload

                    clean_body = re.sub(r'<[^>]+>', ' ', body)
                    otp_match = re.search(r'is\s+(\d{5})', clean_body, re.IGNORECASE)

                    if otp_match:
                        mail.store(latest_id, '+FLAGS', '\\Seen')
                        mail.logout()
                        return otp_match.group(1)

            mail.logout()
        except Exception as e:
            print(f"Error: {str(e)}")

        time.sleep(delay)
    return None

def is_data_available(url):
    try:
        extractor = ChittorgarhIPOExtractor()
        data1 = extractor.extract(url)
        #print(data1)
        data2 = clean_ipo_data(data1)
        #print(data2)
        if "N/A" in data2.get('issue_price_per_share','o'):
            return False
        elif "N/A" in data2.get("ratios",'o').get("pe_ratio",'o'):
            return False
        else:
            return True
    except Exception as e:
        return False
    
def get_last_row(file,sheet):
    path = file
    wb = openpyxl.load_workbook(path)
    ws = wb[sheet]
    column_index = 2
    last_row = 0
    for row in range(ws.max_row, 0, -1):
        if ws.cell(row=row, column=column_index).value is not None:
            last_row = row
            break
    return last_row

def get_last_row_sme():
    path = '../General.xlsx'
    wb = openpyxl.load_workbook(path)
    ws = wb['IPOSME']
    column_index = 2
    last_row = 0
    for row in range(ws.max_row, 0, -1):
        if ws.cell(row=row, column=column_index).value is not None:
            last_row = row
            break
    return last_row+1

def get_last_row_mb():
    path = '../General.xlsx'
    wb = openpyxl.load_workbook(path)
    ws = wb['IPOMB']
    column_index = 2
    last_row = 0
    for row in range(ws.max_row, 0, -1):
        if ws.cell(row=row, column=column_index).value is not None:
            last_row = row
            break
    return last_row+1

#print(is_data_available("https://www.chittorgarh.com/ipo/emiac-technologies-ipo/2766/"))
#print(get_last_row_sme())
#print(get_last_row('../General.xlsx','IPOSME'))0


EMAIL_USER = "prakharvasishtha9@gmail.com"
EMAIL_PASS = "qmtm daun rljp wjrx"
sub = '(SUBJECT "OTP")'
search_query = '(SUBJECT "OTP Generated" UNSEEN)'
#print(get_netbanking_otp(EMAIL_USER, EMAIL_PASS, sub))
#print(otp_shoonya(EMAIL_USER,EMAIL_PASS, search_query, retries=15, delay=7))
#print(get_vix())