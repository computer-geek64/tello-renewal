import datetime as dt
import smtplib
import ssl
from email.message import EmailMessage

from tello_renewal.tello import AccountBalance


class Emailer:
    def __init__(self, smtp_server: str, smtp_port: int, from_email: str) -> None:
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._from_email = from_email

        self._server = smtplib.SMTP(smtp_server, smtp_port)

    def login(self, username: str, password: str) -> None:
        context = ssl.create_default_context()
        self._server.starttls(context=context)
        self._server.login(username, password)

    def send_success_message(self, email_recipient: str, new_balance: AccountBalance) -> None:
        message = EmailMessage()
        message["Subject"] = "Successfully Renewed Your Tello Plan"
        message["From"] = self._from_email
        message["To"] = email_recipient
        message.set_content(f"""Hi {email_recipient},

Your Tello account was renewed successfully.
You now have {new_balance.data}, {new_balance.minutes}, and {new_balance.texts}.

Next renewal is scheduled for {dt.date.today() + dt.timedelta(days=29):%B %-d, %Y}.
""")
        self._server.send_message(message)

    def send_failure_message(self, email_recipient: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Tello Auto Renewal Failed"
        message["From"] = self._from_email
        message["To"] = email_recipient
        message.set_content(f"""Hi {email_recipient},

Your Tello account failed to renew automatically.
Please log in and complete this manually ASAP before tomorrow.

https://tello.com/account/login
""")
