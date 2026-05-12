import datetime
import time
import smtplib, ssl
from urllib.request import *
from email.message import EmailMessage


def Logger(file, StringText="OK", FunctionName="In Function"):
    s = FunctionName + " : " + str(StringText) + " at MM-DD HH:MM :" + str(datetime.datetime.now())[5:16]
    file1="/media/usb0/"+file
    f = open(file1, "a")
    f.write(s)
    f.write("\n")
    f.close()
    print(s)
    #input("Press Enter to continue. ")
    time.sleep(1)
    


def dprint(a=".",b=" ",c=" ",d=" ",e=" ",f=" ",g=" ",h=" "):
    #print("dprint")
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


def TimeNow():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time


def email(email_to="prakharvasishtha9@gmail.com",subject="Subject",message="Message"):
    email_address = "drfrlove@gmail.com"
    email_password = "tmvajnwfcajaophh"
    # create email
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_address
    msg['To'] = email_to
    msg.set_content(message)

    # send email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)


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


def InternetCheck(b="NoSubject"):
    while not (internet_on(b)):
        print("Offline")
        Logger("LogInternet.txt", "Offline", "internet")
        time.sleep(20)
    #print("Online")





#print(Logger("tx.txt","fdsf","fdsff"))
#dprint("hello")
#InternetCheck("PI1-offline")
#email()
# print(internet_on())
# countdown(5)
# print("Completed Running day :at Time :",TimeNow(),"Sleeping for :")
#print(TimeNow())
