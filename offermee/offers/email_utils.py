import os
import re
import smtplib
from typing import List, Optional
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import urllib

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

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """
        Sends an email to the recipient.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            body (str): The content of the email.
            is_html (bool): Indicates whether the content should be interpreted as HTML.
            attachments (Optional[List[str]]): An optional list of file paths to be added as attachments.

        Returns:
            bool: True if the email was successfully sent, otherwise False.
        """
        try:
            if not self.sender_email or not self.sender_password:
                if not self.sender_email:
                    error_msg = "SENDER_EMAIL is not defined."
                elif not self.sender_password:
                    error_msg = "SENDER_PASSWORD is not defined."
                else:
                    error_msg = "SENDER_EMAIL or SENDER_PASSWORD are not defined."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Create the email message
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient
            message["Subject"] = subject

            # Add the main content of the email
            content_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, content_type))

            # Process attachments, if any
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, "rb") as attachment_file:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(attachment_file.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={urllib.parse.quote(os.path.basename(file_path))}",
                            )
                            message.attach(part)
                        except Exception as attach_error:
                            self.logger.error(
                                f"Error attaching file '{file_path}': {attach_error}"
                            )
                            raise ValueError(
                                f"Error attaching file '{file_path}': {attach_error}"
                            )
                    else:
                        self.logger.warning(f"Attachment not found: {file_path}")
                        raise ValueError(f"Attachment not found: {file_path}")

            # Attempt to send the email
            try:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, recipient, message.as_string())
                self.logger.info(f"Email successfully sent to {recipient}.")
                return True
            except Exception as send_error:
                self.logger.error(f"Error sending email to {recipient}: {send_error}")
                raise send_error
        except Exception as error:
            self.logger.error(f"ERROR while trying to send email: {error}")
            # Save the HTML content for error diagnosis
            safe_filename = f"{sanitize_filename(subject)}.html"
            save_html(body, safe_filename, "./email_offers")
            raise error


def sanitize_filename(filename: str) -> str:
    """
    Removes illegal characters from a filename.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    # Replace forbidden characters with an underscore
    sanitized = re.sub(r'[\\/*?:"<>|#]', "_", filename)
    # Remove leading and trailing whitespace
    sanitized = sanitized.strip()
    # Limit the length of the filename, e.g., to 255 characters
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized
