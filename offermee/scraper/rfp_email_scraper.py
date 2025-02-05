import imaplib
import email
from email.header import decode_header
import datetime
from typing import List, Dict, Any, Optional

# Project-specific imports
from offermee.utils.config import Config
from offermee.AI.rfp_processor import RFPProcessor
from offermee.database.facades.main_facades import RFPFacade, ReadFacade
from offermee.database.models.main_models import RFPSource
from offermee.utils.logger import CentralLogger

# Configure logging
logger = CentralLogger.getLogger(__name__)


def connect_to_email(
    server: str, port: int, email_user: str, email_pass: str, mailbox: str = "INBOX"
) -> Optional[imaplib.IMAP4_SSL]:
    """Connects to the specified email server and mailbox.

    Args:
        server (str): The email server address.
        port (int): The email server port.
        email_user (str): The email user.
        email_pass (str): The email password.
        mailbox (str, optional): The mailbox to connect to. Defaults to "INBOX".

    Returns:
        Optional[imaplib.IMAP4_SSL]: The IMAP4_SSL object if successful, None otherwise.
    """
    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(email_user, email_pass)
        mail.select(mailbox)
        logger.info(f"Successfully connected to the mailbox '{mailbox}'.")
        return mail
    except imaplib.IMAP4.error as e:
        logger.error(f"Error connecting to the email server: {e}")
        return None
    except Exception as e:
        logger.error(f"Error connecting to the email server: {e}")
        return None


def fetch_emails(
    mail: imaplib.IMAP4_SSL,
    since_date: str,
    subject_filter: str = None,
    sender_filter: str = None,
) -> List[bytes]:
    try:
        # Search for emails since the specified date
        status, messages = mail.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            logger.error("Error searching for emails.")
            return []

        email_ids = messages[0].split()
        logger.info(f"Found emails since {since_date}: {len(email_ids)}")

        filtered_emails = []
        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                logger.warning(f"Error fetching email ID {eid}. Skipping.")
                continue
            msg = email.message_from_bytes(msg_data[0][1])

            # Decode the subject
            subject, encoding = decode_header(msg.get("Subject"))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            # Decode the sender
            from_, encoding = decode_header(msg.get("From"))[0]
            if isinstance(from_, bytes):
                from_ = from_.decode(encoding if encoding else "utf-8")

            # Filter by subject and sender if specified
            if subject_filter and subject_filter not in subject:
                continue
            if sender_filter and sender_filter not in from_:
                continue

            filtered_emails.append(msg_data[0][1])

        logger.info(f"Remaining emails after filtering: {len(filtered_emails)}")
        return filtered_emails
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return []


def parse_email(msg_bytes: bytes) -> Dict[str, Any]:
    try:
        msg = email.message_from_bytes(msg_bytes)

        # Decode the subject
        subject, encoding = decode_header(msg.get("Subject"))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")

        # Decode the sender
        from_, encoding = decode_header(msg.get("From"))[0]
        if isinstance(from_, bytes):
            from_ = from_.decode(encoding if encoding else "utf-8")

        # Extract the date
        date_str = msg.get("Date")
        try:
            # Parse the date into a datetime object
            email_date = email.utils.parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Unknown date format in email: {date_str}. Error: {e}")
            email_date = None

        # Extract the email content
        if msg.is_multipart():
            parts = msg.walk()
            body = ""
            for part in parts:
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if (
                    content_type == "text/plain"
                    and "attachment" not in content_disposition
                ):
                    charset = part.get_content_charset() or "utf-8"
                    body += part.get_payload(decode=True).decode(
                        charset, errors="ignore"
                    )
        else:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="ignore"
            )

        return {
            "subject": subject,
            "from": from_,
            "body": body,
            "date": str(email_date),  # Add timestamp
        }
    except Exception as e:
        logger.error(f"Error parsing the email: {e}")
        return {}


def process_email(rfp_data: Dict[str, Any], operator: str):
    try:
        processor = RFPProcessor()
        result = processor.analyze_rfp(rfp_data["body"])
        if not result or "project" not in result:
            logger.warning("AI analysis did not return a valid 'project' structure.")
            return

        rfp: Dict[str, Any] = result["project"]
        # Check if the RFP already exists
        rfp_record = ReadFacade.get_source_rule_unique_rfp_record(
            source=RFPSource.EMAIL,
            contact_person_email=rfp.get("contact_person_email"),
            title=rfp.get("title"),
        )
        if rfp_record:
            logger.info(
                f"Skipping RFP '{rfp.get('title')}' of '{rfp.get('contact_person_email')}' that already exists in db."
            )
            return

        # Transform and save the new project
        rfp["source"] = RFPSource.EMAIL
        RFPFacade.create(rfp, operator)
        logger.info(
            f"New RFP '{rfp.get('title')}' of '{rfp.get('contact_person_email')}' successfully saved to db."
        )
    except Exception as e:
        logger.error(f"ERROR while processing the Email: {e}")


def scrap_rfps_from_email(since_days: int = 2):
    # Load configuration
    config = Config.get_instance().get_config_data()
    email_user = config.imap_email
    email_pass = config.imap_password
    server = config.imap_server
    port = config.imap_port
    mailbox = config.rfp_mailbox
    subject_filter = config.rfp_email_subject_filter
    sender_filter = config.rfp_email_sender_filter
    operator = config.current_user

    # Connect to the email server
    mail = connect_to_email(server, port, email_user, email_pass, mailbox)

    # Define the date (last 48 hours)
    since_date = (
        datetime.datetime.now() - datetime.timedelta(days=since_days)
    ).strftime("%d-%b-%Y")

    # Fetch relevant emails
    emails = fetch_emails(mail, since_date, subject_filter, sender_filter)

    # Process each email
    for msg_bytes in emails:
        rfp_data = parse_email(msg_bytes)
        if rfp_data:
            process_email(rfp_data, operator)

    # Logout from the email server
    mail.logout()
    logger.info("Email scraping completed.")
