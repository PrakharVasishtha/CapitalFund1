from Base import *

def withdraw_bank_to_kite():
    EMAIL_USER = "prakharvasishtha9@gmail.com"
    EMAIL_PASS = "qmtm daun rljp wjrx"
    sub1 = '(SUBJECT "SMS2EMAIL" UNSEEN)'
    otp = get_netbanking_otp(EMAIL_USER, EMAIL_PASS, sub1)
    print(otp)
    
