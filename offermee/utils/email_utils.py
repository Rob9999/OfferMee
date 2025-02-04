import os
import re
import smtplib
import imaplib
import time
import enum
import email
from email.header import decode_header
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib
from typing import List, Optional, Tuple, Dict, Any

from offermee.config import Config
from offermee.htmls.save_utils import save_html
from offermee.logger import CentralLogger


class EmailStatus(enum.Enum):
    SEEN = "SEEN"
    UNSEEN = "UNSEEN"


class EmailUtils:
    """
    Utility class for sending emails and performing full IMAP operations
    for a web email application.
    """

    def __init__(self):
        self.logger = CentralLogger.getLogger(__name__)
        current_config = Config.get_instance().get_config_data()
        # SMTP configuration
        self.sender_email = current_config.sender_email
        self.sender_password = current_config.sender_password
        self.smtp_server = current_config.smtp_server
        self.smtp_port = current_config.smtp_port
        # IMAP configuration
        self.imap_server = current_config.imap_server
        self.imap_port = current_config.imap_port
        self.imap_email = current_config.imap_email
        self.imap_password = current_config.imap_password

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
        """
        try:
            if not self.sender_email or not self.sender_password:
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

            # Process attachments if provided
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

            # Attempt to send the email via SMTP
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, message.as_string())
            self.logger.info(f"Email successfully sent to {recipient}.")

            # Save a copy to the IMAP 'Sent' folder.
            self.save_to_sent_folder(message.as_string(), folder="Sent")

            return True
        except Exception as error:
            self.logger.error(f"ERROR while trying to send email: {error}")
            safe_filename = f"{sanitize_filename(subject)}.html"
            save_html(body, safe_filename, "./email_offers")
            raise error

    def _get_imap_connection(self) -> imaplib.IMAP4_SSL:
        """
        Creates and returns a logged-in IMAP connection using SSL.

        Returns:
            imaplib.IMAP4_SSL: A logged-in IMAP connection.
        """
        try:
            imap_conn = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap_conn.login(self.imap_email, self.imap_password)
            self.logger.info("IMAP connection established.")
            return imap_conn
        except Exception as imap_error:
            self.logger.error(f"Error connecting to IMAP server: {imap_error}")
            raise imap_error

    def save_to_sent_folder(self, email_message: str, folder: str = "Sent") -> None:
        """
        Saves (appends) the given email message to the specified IMAP folder.
        If the server requires a namespace prefix (e.g., "INBOX."), it is automatically added.

        Args:
            email_message (str): The full raw email message as a string.
            folder (str): The target folder name (default is 'Sent').
        """
        try:
            if not folder.upper().startswith("INBOX"):
                folder = f"INBOX.{folder}"
            imap_conn = self._get_imap_connection()
            date_time = imaplib.Time2Internaldate(time.time())
            result, response = imap_conn.append(
                folder, "", date_time, email_message.encode("utf-8")
            )
            if result != "OK":
                raise Exception(
                    f"Failed to append message to folder {folder}: {response}"
                )
            self.logger.info(f"Email message saved to folder '{folder}'.")
            imap_conn.logout()
        except Exception as e:
            self.logger.error(f"Error saving email to IMAP folder '{folder}': {e}")
            raise e

    def move_email_to_folder(
        self, mailbox: str, email_uid: str, target_folder: str
    ) -> None:
        """
        Moves an email from one folder to another on the IMAP server.
        """
        try:
            imap_conn = self._get_imap_connection()
            imap_conn.select(mailbox)
            result, _ = imap_conn.uid("MOVE", email_uid, target_folder)
            if result != "OK":
                raise Exception(
                    f"Failed to move email UID {email_uid} to folder {target_folder}"
                )
            self.logger.info(
                f"Email UID {email_uid} moved to folder '{target_folder}'."
            )
            imap_conn.logout()
        except Exception as e:
            self.logger.error(
                f"Error moving email UID {email_uid} to folder '{target_folder}': {e}"
            )
            raise e

    def change_email_state(
        self, mailbox: str, email_uid: str, flag: str = r"\Seen", mark_as: bool = True
    ) -> None:
        """
        Changes the state (flags) of an email. For example, marking an email as seen/unseen.
        """
        try:
            imap_conn = self._get_imap_connection()
            imap_conn.select(mailbox)
            action = "+FLAGS" if mark_as else "-FLAGS"
            result, _ = imap_conn.uid("STORE", email_uid, action, flag)
            if result != "OK":
                raise Exception(
                    f"Failed to update email UID {email_uid} flag '{flag}' with action '{action}'"
                )
            self.logger.info(
                f"Email UID {email_uid} flag '{flag}' updated (mark_as={mark_as})."
            )
            imap_conn.logout()
        except Exception as e:
            self.logger.error(f"Error updating flag for email UID {email_uid}: {e}")
            raise e

    def list_mailboxes(self) -> List[str]:
        """
        Lists all available mailboxes/folders.

        Returns:
            List[str]: A list of mailbox names.
        """
        try:
            imap_conn = self._get_imap_connection()
            status, mailboxes = imap_conn.list()
            if status != "OK":
                raise Exception("Failed to retrieve mailboxes.")
            mailbox_list = []
            for mailbox in mailboxes:
                parts = mailbox.decode().split(' "/" ')
                if len(parts) == 2:
                    mailbox_list.append(parts[1].strip('"'))
            self.logger.info("Retrieved mailbox list.")
            imap_conn.logout()
            return mailbox_list
        except Exception as e:
            self.logger.error(f"Error listing mailboxes: {e}")
            raise e

    def _get_status_from_response(self, response_data: bytes) -> EmailStatus:
        """
        Parses a FETCH response string to determine the email status based on FLAGS.

        Args:
            response_data (bytes): The byte string from the FETCH response.

        Returns:
            EmailStatus: SEEN if the '\\Seen' flag is present; otherwise UNSEEN.
        """
        try:
            decoded = response_data.decode("utf-8")
            flags_match = re.search(r"FLAGS \((.*?)\)", decoded)
            if flags_match:
                flags = flags_match.group(1).split()
                if r"\Seen" in flags:
                    return EmailStatus.SEEN
            return EmailStatus.UNSEEN
        except Exception:
            return EmailStatus.UNSEEN

    def fetch_emails(
        self, mailbox: str = "INBOX"
    ) -> List[Tuple[str, str, EmailStatus]]:
        """
        Fetches a list of email UIDs, subjects, and statuses from the specified mailbox.
        """
        try:
            imap_conn = self._get_imap_connection()
            imap_conn.select(mailbox)
            status, data = imap_conn.uid("SEARCH", None, "ALL")
            if status != "OK":
                raise Exception("Failed to search emails.")
            email_uids = data[0].split()
            emails = []
            for uid in email_uids:
                status, msg_data = imap_conn.uid(
                    "FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)] FLAGS)"
                )
                if status != "OK":
                    continue
                subject = ""
                email_status = EmailStatus.UNSEEN
                for response in msg_data:
                    if isinstance(response, tuple):
                        header_msg = email.message_from_bytes(response[1])
                        subject = header_msg.get("Subject", "")
                        email_status = self._get_status_from_response(response[0])
                emails.append((uid.decode(), subject, email_status))
            self.logger.info(f"Fetched {len(emails)} emails from {mailbox}.")
            imap_conn.logout()
            return emails
        except Exception as e:
            self.logger.error(f"Error fetching emails from {mailbox}: {e}")
            raise e

    def fetch_email(self, mailbox: str, email_uid: str) -> Tuple[str, EmailStatus]:
        """
        Fetches the full raw email content and status for a given UID from the specified mailbox.
        """
        try:
            imap_conn = self._get_imap_connection()
            imap_conn.select(mailbox)
            status, data = imap_conn.uid("FETCH", email_uid, "(RFC822 FLAGS)")
            if status != "OK":
                raise Exception(f"Failed to fetch email UID {email_uid} from {mailbox}")
            raw_email = data[0][1].decode("utf-8")
            email_status = self._get_status_from_response(data[0][0])
            self.logger.info(f"Fetched email UID {email_uid} from {mailbox}.")
            imap_conn.logout()
            return raw_email, email_status
        except Exception as e:
            self.logger.error(
                f"Error fetching email UID {email_uid} from {mailbox}: {e}"
            )
            raise e

    def delete_email(self, mailbox: str, email_uid: str) -> None:
        """
        Deletes an email by marking it as deleted and expunging the mailbox.
        """
        try:
            imap_conn = self._get_imap_connection()
            imap_conn.select(mailbox)
            result, _ = imap_conn.uid("STORE", email_uid, "+FLAGS", r"(\Deleted)")
            if result != "OK":
                raise Exception(f"Failed to mark email UID {email_uid} as deleted.")
            imap_conn.expunge()
            self.logger.info(f"Email UID {email_uid} deleted from {mailbox}.")
            imap_conn.logout()
        except Exception as e:
            self.logger.error(
                f"Error deleting email UID {email_uid} from {mailbox}: {e}"
            )
            raise e

    def create_folder(self, folder_name: str) -> None:
        """
        Creates a new folder/mailbox on the IMAP server.
        """
        try:
            imap_conn = self._get_imap_connection()
            result, _ = imap_conn.create(folder_name)
            if result != "OK":
                raise Exception(f"Failed to create folder '{folder_name}'.")
            self.logger.info(f"Folder '{folder_name}' created successfully.")
            imap_conn.logout()
        except Exception as e:
            self.logger.error(f"Error creating folder '{folder_name}': {e}")
            raise e

    # --- New Methods to Replace Standalone Scraper Functions ---

    def search_emails(
        self,
        mailbox: str,
        since_date: str,
        subject_filter: Optional[str] = None,
        sender_filter: Optional[str] = None,
    ) -> List[bytes]:
        """
        Searches for emails in the specified mailbox based on a SINCE date and optional subject/sender filters.

        Args:
            mailbox (str): The mailbox (folder) to search.
            since_date (str): The date in format "DD-MMM-YYYY" (e.g. "01-Jan-2025") to search emails since.
            subject_filter (Optional[str]): Optional substring to filter by email subject.
            sender_filter (Optional[str]): Optional substring to filter by sender.

        Returns:
            List[bytes]: A list of raw email messages as bytes that match the criteria.
        """
        try:
            imap_conn = self._get_imap_connection()
            imap_conn.select(mailbox)
            status, messages = imap_conn.search(None, f'(SINCE "{since_date}")')
            if status != "OK":
                raise Exception("Failed to search emails.")
            email_ids = messages[0].split()
            self.logger.info(
                f"Found {len(email_ids)} emails in {mailbox} SINCE {since_date}."
            )
            filtered_emails = []
            for eid in email_ids:
                status, msg_data = imap_conn.fetch(eid, "(RFC822)")
                if status != "OK" or not msg_data:
                    self.logger.warning(
                        f"Failed to fetch email id {eid.decode()}. Skipping."
                    )
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode subject and sender for filtering
                subject, enc = decode_header(msg.get("Subject"))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(enc if enc else "utf-8", errors="ignore")
                from_, enc = decode_header(msg.get("From"))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(enc if enc else "utf-8", errors="ignore")

                if subject_filter and subject_filter not in subject:
                    continue
                if sender_filter and sender_filter not in from_:
                    continue

                filtered_emails.append(raw_email)
            self.logger.info(f"After filtering, {len(filtered_emails)} emails remain.")
            imap_conn.logout()
            return filtered_emails
        except Exception as e:
            self.logger.error(f"Error during email search in {mailbox}: {e}")
            raise e

    def parse_email(self, raw_email: bytes) -> Dict[str, Any]:
        """
        Parses a raw email message (bytes) and returns a structured dictionary.

        Args:
            raw_email (bytes): The raw email message.

        Returns:
            Dict[str, Any]: A dictionary with keys 'subject', 'from', 'body', and 'date'.
        """
        try:
            msg = email.message_from_bytes(raw_email)
            # Decode subject
            subject, enc = decode_header(msg.get("Subject"))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(enc if enc else "utf-8", errors="ignore")
            # Decode sender
            from_, enc = decode_header(msg.get("From"))[0]
            if isinstance(from_, bytes):
                from_ = from_.decode(enc if enc else "utf-8", errors="ignore")
            # Parse date
            date_str = msg.get("Date")
            try:
                email_date = email.utils.parsedate_to_datetime(date_str)
            except Exception as e:
                self.logger.warning(f"Unknown date format '{date_str}': {e}")
                email_date = None
            # Extract email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if (
                        content_type == "text/plain"
                        and "attachment" not in content_disposition
                    ):
                        charset = part.get_content_charset() or "utf-8"
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode(charset, errors="ignore")
            else:
                charset = msg.get_content_charset() or "utf-8"
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors="ignore")
            return {
                "subject": subject,
                "from": from_,
                "body": body,
                "date": str(email_date) if email_date else None,
            }
        except Exception as e:
            self.logger.error(f"Error parsing email: {e}")
            return {}


def sanitize_filename(filename: str) -> str:
    """
    Removes illegal characters from a filename and limits its length.
    """
    sanitized = re.sub(r'[\\/*?:"<>|#]', "_", filename)
    sanitized = sanitized.strip()
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized
