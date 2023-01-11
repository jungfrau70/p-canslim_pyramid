# Python code to illustrate Sending mail with attachments
# from your Gmail account 
# https://support.google.com/mail/answer/185833?hl=en

# libraries to be imported
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
   
# From: and To:
fromaddr = "inhwan.jung@gmail.com"
toaddr = "9368265@ict-companion.com"

# open the file to be sent 
filename = f"{end_date}_findings.csv"
   

def send(filename, fromaddr, password="xdelejgdqidlpcxq"):
    
    # instance of MIMEMultipart
    msg = MIMEMultipart()

    # storing the senders email address  
    msg['From'] = fromaddr

    # storing the receivers email address 
    msg['To'] = toaddr

    # storing the subject 
    msg['Subject'] = "Today' Cup with handle"

    # string to store the body of the mail
    body = "Today' Cup with handle"

    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    attachment = open(filename, "rb")

    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')

    # To change the payload into encoded form
    p.set_payload((attachment).read())

    # encode into base64
    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    # attach the instance 'p' to instance 'msg'
    msg.attach(p)

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    # s = smtplib.SMTP_SSL('smtp.googlemail.com', 465)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(fromaddr, password)

    # Converts the Multipart msg into a string
    text = msg.as_string()

    # sending the mail
    s.sendmail(fromaddr, toaddr, text)

    # terminating the session
    s.quit()
        
if exists(filename):
    sendmail(filename, fromaddr)
else:
    print("Not exists")
