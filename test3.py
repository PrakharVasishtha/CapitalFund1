import imaplib
import email
import re
import time


def get_netbanking_otp(retries=15, delay=7):

    EMAIL_USER = "prakharvasishtha9@gmail.com"
    EMAIL_PASS = "qmtm daun rljp wjrx"
    for i in range(retries):
        print(f"Attempt {i + 1}: Searching for Net Banking OTP...")
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")

            # --- SEARCH CRITERIA ---
            # Looks for emails with the specific subject
            # 'UNSEEN' ensures we don't grab an old, already-used OTP
            search_query = '(SUBJECT "Net banking login" UNSEEN)'
            status, messages = mail.search(None, search_query)

            if status == "OK" and messages[0]:
                # Get the most recent email ID
                latest_id = messages[0].split()[-1]
                _, msg_data = mail.fetch(latest_id, "(RFC822)")

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                else:
                    body = msg.get_payload(decode=True).decode()

                # Search for 6-digit OTP
                otp_match = re.search(r'\b\d{6}\b', body)

                if otp_match:
                    mail.logout()
                    return otp_match.group(0)

            mail.logout()
        except Exception as e:
            print(f"Connection error: {e}")

        # Wait for the email to actually arrive
        time.sleep(delay)

    return None


# Usage
otp = get_netbanking_otp()
if otp:
    print(f"Successfully fetched OTP: {otp}")
else:
    print("Failed to find a new Net Banking OTP.")