import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging


class EmailUtils:
    """
    Utility class for sending emails.
    """

    def __init__(self):
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 465))

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def send_email(self, recipient, subject, body, html=False):
        """
        Sends an email to the recipient.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            body (str): The content of the email.
            html (bool): Indicates whether the content is HTML.
        """
        if not self.sender_email or not self.sender_password:
            self.logger.error("SENDER_EMAIL or SENDER_PASSWORD are not defined.")
            return

        message = MIMEMultipart("alternative")
        message["From"] = self.sender_email
        message["To"] = recipient
        message["Subject"] = subject

        part = MIMEText(body, "html" if html else "plain")
        message.attach(part)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, message.as_string())
            self.logger.info(f"Email successfully sent to {recipient}.")
        except Exception as e:
            self.logger.error(f"Error sending email to {recipient}: {e}")
