from Base import *

def withdraw_bank_to_kite():
    EMAIL_PASS = "qmtm daun rljp wjrx"
    sub1 = '(SUBJECT "JD-KOTAKB-T" UNSEEN)'
    otp = get_netbanking_otp(EMAIL_USER, EMAIL_PASS, sub1)
    print(otp)
    
