import imaplib
import email
from email.header import decode_header
import datetime
from typing import List, Dict, Any, Optional

# Deine projektspezifischen Importe
from offermee.config import Config
from offermee.AI.project_processor import ProjectProcessor
from offermee.database.facades.main_facades import ProjectFacade
from offermee.database.transformers.project_model_transformer import json_to_db
from offermee.logger import CentralLogger

# Konfiguriere Logging
logger = CentralLogger.getLogger(__name__)


def connect_to_email(
    server: str, port: int, email_user: str, email_pass: str, mailbox: str = "INBOX"
) -> Optional[imaplib.IMAP4_SSL]:
    """Connects to the specified email server and mailbox.

    Args:
        server (str): _description_
        port (int): _description_
        email_user (str): _description_
        email_pass (str): _description_
        mailbox (str, optional): _description_. Defaults to "INBOX".

    Returns:
        Optional[imaplib.IMAP4_SSL]: The IMAP4_SSL object if successful, None otherwise.
    """
    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(email_user, email_pass)
        mail.select(mailbox)
        logger.info(f"Erfolgreich mit dem Postfach '{mailbox}' verbunden.")
        return mail
    except imaplib.IMAP4.error as e:
        logger.error(f"Fehler beim Verbinden mit dem E-Mail-Server: {e}")
        # sys.exit(1)
        return None
    except Exception as e:
        logger.error(f"Fehler beim Verbinden mit dem E-Mail-Server: {e}")
        return None


def fetch_emails(
    mail: imaplib.IMAP4_SSL,
    since_date: str,
    subject_filter: str = None,
    sender_filter: str = None,
) -> List[bytes]:
    try:
        # Suche nach E-Mails seit dem angegebenen Datum
        status, messages = mail.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            logger.error("Fehler beim Suchen von E-Mails.")
            return []

        email_ids = messages[0].split()
        logger.info(f"Gefundene E-Mails seit {since_date}: {len(email_ids)}")

        filtered_emails = []
        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                logger.warning(f"Fehler beim Abrufen der E-Mail-ID {eid}. Überspringe.")
                continue
            msg = email.message_from_bytes(msg_data[0][1])

            # Dekodiere den Betreff
            subject, encoding = decode_header(msg.get("Subject"))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            # Dekodiere den Absender
            from_, encoding = decode_header(msg.get("From"))[0]
            if isinstance(from_, bytes):
                from_ = from_.decode(encoding if encoding else "utf-8")

            # Filtere nach Betreff und Absender, falls angegeben
            if subject_filter and subject_filter not in subject:
                continue
            if sender_filter and sender_filter not in from_:
                continue

            filtered_emails.append(msg_data[0][1])

        logger.info(f"Nach Filterung übriggebliebene E-Mails: {len(filtered_emails)}")
        return filtered_emails
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von E-Mails: {e}")
        return []


def parse_email(msg_bytes: bytes) -> Dict[str, Any]:
    try:
        msg = email.message_from_bytes(msg_bytes)

        # Betreff dekodieren
        subject, encoding = decode_header(msg.get("Subject"))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")

        # Absender dekodieren
        from_, encoding = decode_header(msg.get("From"))[0]
        if isinstance(from_, bytes):
            from_ = from_.decode(encoding if encoding else "utf-8")

        # Datum extrahieren
        date_str = msg.get("Date")
        try:
            # Parse das Datum in ein datetime-Objekt
            email_date = email.utils.parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(
                f"Unbekanntes Datumsformat in E-Mail: {date_str}. Fehler: {e}"
            )
            email_date = None

        # Inhalt der E-Mail extrahieren
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
            "date": str(email_date),  # Zeitstempel hinzufügen
        }
    except Exception as e:
        logger.error(f"Fehler beim Parsen der E-Mail: {e}")
        return {}


def process_email(rfp_data: Dict[str, Any], operator: str):
    try:
        processor = ProjectProcessor()
        result = processor.analyze_project(rfp_data["body"])
        if not result or "project" not in result:
            logger.warning("AI-Analyse lieferte keine gültige 'project'-Struktur.")
            return

        # Überprüfe, ob das Projekt bereits existiert
        original_link = result["project"].get("original-link")
        if original_link:
            existing = ProjectFacade.get_first_by({"original_link": original_link})
            if existing:
                logger.info(
                    f"Projekt mit original_link '{original_link}' existiert bereits. Überspringe."
                )
                return

        # Transformiere und speichere das neue Projekt
        new_project = json_to_db({"project": result["project"]}).to_dict()
        ProjectFacade.create(new_project, operator)
        logger.info(
            f"Neues Projekt '{new_project.get('title')}' wurde erfolgreich gespeichert."
        )
    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten der E-Mail: {e}")


def scrap_rfps_from_email(since_days: int = 2):
    # Lade Konfiguration
    config = Config.get_instance().get_config_data()
    email_user = config.imap_email
    email_pass = config.imap_password
    server = config.imap_server
    port = config.imap_port
    mailbox = config.rfp_mailbox
    subject_filter = config.rfp_email_subject_filter
    sender_filter = config.rfp_email_sender_filter
    operator = config.current_user

    # Verbinde mit dem E-Mail-Server
    mail = connect_to_email(server, port, email_user, email_pass, mailbox)

    # Definiere das Datum (letzte 48 Stunden)
    since_date = (
        datetime.datetime.now() - datetime.timedelta(days=since_days)
    ).strftime("%d-%b-%Y")

    # Hole relevante E-Mails
    emails = fetch_emails(mail, since_date, subject_filter, sender_filter)

    # Verarbeite jede E-Mail
    for msg_bytes in emails:
        rfp_data = parse_email(msg_bytes)
        if rfp_data:
            process_email(rfp_data, operator)

    # Logout vom E-Mail-Server
    mail.logout()
    logger.info("E-Mail-Scraping abgeschlossen.")
