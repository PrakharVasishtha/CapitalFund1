import imaplib
import re
from email.utils import parsedate_to_datetime
from email.header import decode_header  # ← NEW
import datetime
import time
from email import message_from_bytes


def get_mstock_otp(EMAIL_USER, EMAIL_PASS, search_query, retries=15, delay=5, max_emails_to_check=3):
    """
    Checks newest 5 matching emails → decodes subject properly → finds 6-digit OTP
    Only considers emails ≤ 2 minutes old.
    """
    time.sleep(10)
    for attempt in range(retries):
        print(f"Attempt {attempt + 1}: Checking newest {max_emails_to_check} emails...")

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")

            status, messages = mail.search(None, search_query)

            if status != "OK" or not messages[0]:
                print("No matching emails.")
                mail.logout()
                time.sleep(delay)
                continue

            all_ids = messages[0].split()
            recent_ids = all_ids[-max_emails_to_check:] if len(all_ids) >= max_emails_to_check else all_ids

            print(f"Found {len(all_ids)} total → checking newest {len(recent_ids)}")

            now_utc = datetime.datetime.now(datetime.timezone.utc)

            for msg_id in reversed(recent_ids):
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                msg = message_from_bytes(msg_data[0][1])

                # Age check
                date_str = msg.get("Date")
                if not date_str:
                    continue
                try:
                    email_time = parsedate_to_datetime(date_str)
                    if email_time.tzinfo is None:
                        email_time = email_time.replace(tzinfo=datetime.timezone.utc)
                    age_seconds = (now_utc - email_time).total_seconds()
                    if age_seconds > 120 or age_seconds < -30:
                        continue
                except:
                    continue

                # ── Properly decode subject ──
                subject_raw = msg.get("Subject", "")
                if not subject_raw:
                    continue

                # Decode MIME header (handles =?utf-8?B?...?= etc.)
                decoded_parts = []
                for part, charset in decode_header(subject_raw):
                    if isinstance(part, bytes):
                        try:
                            decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
                        except:
                            decoded_parts.append(part.decode('ascii', errors='replace'))
                    else:
                        decoded_parts.append(part)

                subject = ''.join(decoded_parts).strip()

                print(f"  Decoded subject: {subject}")

                # Find OTP
                match = re.search(r'\b(\d{6})\b', subject)
                if match:
                    otp = match.group(1)
                    print(f"→ OTP found: {otp}")
                    mail.store(msg_id, '+FLAGS', '\\Seen')
                    mail.logout()
                    return otp

            mail.logout()

        except Exception as e:
            print(f"Error: {str(e)}")

        time.sleep(delay)

    print("No OTP found in recent emails.")
    return None
'''
EMAIL_USER = "prakharvasishtha9@gmail.com"
EMAIL_PASS = "qmtm daun rljp wjrx"
search_query = '(SUBJECT "Your login OTP")'

#print(get_mstock_otp(EMAIL_USER, EMAIL_PASS, search_query, retries=15, delay=5))
'''