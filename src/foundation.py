import datetime
import time
import smtplib, ssl
from urllib.request import *
from email.message import EmailMessage
import os

def logger(file, StringText="OK", FunctionName="In Function"):
    s = FunctionName + " : " + str(StringText) + " at MM-DD HH:MM :" + str(datetime.datetime.now())[5:16]
    f = open(file, "a")
    f.write(s)
    f.write("\n")
    f.close()
    print(s)
    #input("Press Enter to continue. ")
    time.sleep(1)
    
def dprint(a=".",b=" ",c=" ",d=" ",e=" ",f=" ",g=" ",h=" "):
    #print("dprint")
    #i=0 for production, i = 1 for debugging.
    i=1
    if i==1:
        print(str(a)+" "+str(b)+" "+str(c)+" "+str(d)+" "+str(e)+" "+str(f)+" "+str(g)+" "+str(h))
    
def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1
    # print("Over")

def timenow():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time

import smtplib
from email.message import EmailMessage

def send_email(email_address = "vasistcapital@gmail.com",sub_send = "default",content_send = "default"):
    email_address = "vasistcapital@gmail.com"
    email_password = "tmvajnwfcajaophh"
    
    msg = EmailMessage()
    msg['Subject'] = sub_send
    msg['From'] = email_address
    msg['To'] = "prakharvasishtha9@gmail.com"
    msg.set_content(content_send)

    try:
        # Switch to SMTP and port 587
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()      # Identify yourself to the server
            smtp.starttls()  # Encrypt the connection
            smtp.ehlo()      # Re-identify as an encrypted connection
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_address, email_password)
                smtp.send_message(msg)
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error: {e}")
            logger("system.txt",sub_send,"send_email")

def send_email_with_excel():
    email_address = "vasistcapital@gmail.com"
    email_password = "tmvajnwfcajaophh"
    
    msg = EmailMessage()
    msg['Subject'] = "Excel Report Attached"
    msg['From'] = email_address
    msg['To'] = "prakharvasishtha9@gmail.com"
    msg.set_content("Please find the attached Excel file.")
    file_path = '../General.xlsx'
    # --- ATTACHMENT LOGIC ---
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)
        
        msg.add_attachment(
            file_data,
            maintype='application',
            subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', # Standard for .xlsx
            filename=file_name
        )
    except FileNotFoundError:
        print("The file was not found. Check the file path!")
        return

    # --- SENDING LOGIC ---
    try:
        # Using Port 587 as it's often more reliable for timeouts
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print(f"Email sent successfully with {file_name}!")
    except Exception as e:
        print(f"Error: {e}")
        logger("system.txt","send_email_with_excel","send_email_with_excel")

def internet_on(a1="nosub"):
    try:
        urlopen('http://www.google.com/', timeout=1)
        return True
    except:
        try:
            print("sending email")
            #email("prakharvasishtha9@gmail.com",a1,"Internet Not Working")
        except:
            print("Error in SendEmail while run internet_on")
            #Logger("LogError.txt", "Error in sending email", "internet_on")
        return False

def internetcheck(b="NoSubject"):
    while not (internet_on(b)):
        print("Offline")
        Logger("LogInternet.txt", "Offline", "internet")
        time.sleep(20)
    #print("Online")

#print(logger("tx.txt","fdsf","fdsff"))
#dprint("hello")
#internetcheck("PI1-offline")
#send_email()
# Call the function with the path to your file
# Example: r"C:\Users\Name\Documents\data.xlsx"
send_email_with_excel()
# print(internet_on())
# countdown(5)
# print("Completed Running day :at Time :",TimeNow(),"Sleeping for :")
#print(timenow())
