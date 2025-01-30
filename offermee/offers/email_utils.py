import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

from offermee.config import Config
from offermee.htmls.save_utils import save_html
from offermee.logger import CentralLogger


class EmailUtils:
    """
    Utility class for sending emails.
    """

    def __init__(self):
        self.logger = CentralLogger.getLogger(__name__)
        current_config = Config.get_instance().get_config_data()
        self.sender_email = current_config.sender_email
        self.sender_password = current_config.sender_password
        self.smtp_server = current_config.smtp_server
        self.smtp_port = current_config.smtp_port

    def send_email(self, recipient, subject, body, is_html=False):
        """
        Sends an email to the recipient.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            body (str): The content of the email.
            html (bool): Indicates whether the content is HTML.
        """
        try:
            if not self.sender_email or not self.sender_password:
                self.logger.error("SENDER_EMAIL or SENDER_PASSWORD are not defined.")
                raise ValueError("SENDER_EMAIL or SENDER_PASSWORD are not defined.")

            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient
            message["Subject"] = subject

            part = MIMEText(body, "html" if is_html else "plain")
            message.attach(part)

            try:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, recipient, message.as_string())
                self.logger.info(f"Email successfully sent to {recipient}.")
                return True
            except Exception as e:
                raise e
        except Exception as e:
            self.logger.error(f"Error sending email to {recipient}: {e}")
            save_html(body, f"{sanitize_filename(subject)}.html", "./email_offers")
            return False


def sanitize_filename(filename: str) -> str:
    # Ersetze verbotene Zeichen durch Unterstrich
    # Hier eine einfache Regex, die die meisten Sonderzeichen ersetzt
    # Passen Sie die Regex an, falls weitere Zeichen ausgeschlossen werden sollen.
    sanitized = re.sub(r'[\\/*?:"<>|#]', "_", filename)

    # Entferne führende und endende Leerzeichen
    sanitized = sanitized.strip()

    # Optionale weitere Anpassungen:
    # - Begrenzung der Länge (zum Beispiel auf 255 Zeichen)
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
