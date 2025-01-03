import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailUtils:

    @staticmethod
    def send_email(recipient, subject, body):
        """
        Sendet eine E-Mail an den Empfänger.

        Args:
            recipient (str): Die E-Mail-Adresse des Empfängers.
            subject (str): Der Betreff der E-Mail.
            body (str): Der Inhalt der E-Mail.
        """
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")

        if not sender_email or not sender_password:
            print(
                "SENDER_EMAIL oder SENDER_PASSWORD sind nicht in der .env-Datei definiert."
            )
            return

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient, message.as_string())
            print(f"Email erfolgreich an {recipient} gesendet.")
        except Exception as e:
            print(f"Fehler beim Senden der Email: {e}")
