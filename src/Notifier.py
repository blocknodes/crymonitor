import smtplib 
from email.mime.text import MIMEText

class EmailNotifier():
    def __init__(self, sender, recvers, smtp_url, smtp_port,  smtp_passwd):
        self.sender = sender
        self.recvers = recvers
        self.smtp = smtplib.SMTP_SSL(smtp_url, smtp_port)
        self.smtp.login(sender, smtp_passwd)

    def send(self, subject, content):
        message = MIMEText(content,"plain","utf-8")
        message['Subject'] = subject 
        message['To'] = "shiba fan" 
        message['From'] = self.sender
        try:
            self.smtp.sendmail(self.sender, self.recvers, message.as_string())
        except Exception:
            pass
        


