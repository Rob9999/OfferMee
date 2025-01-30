import datetime
from datetime import timedelta
import logging

from offermee.database.facades.main_facades import OfferFacade
from offermee.database.models.main_models import OfferStatus
from offermee.offers.email_utils import EmailUtils

# Configuration
FOLLOW_UP_DELAY_DAYS = 3  # After how many days a follow-up is sent
MAX_FOLLOWUPS = 2  # Maximum number of follow-ups to be sent


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    email_utils = EmailUtils()

    # Current date and timestamp when a follow-up would be due
    now = datetime.datetime.now()
    threshold_date = now - timedelta(days=FOLLOW_UP_DELAY_DAYS)

    try:
        # Load all offers with status SENT
        offers_to_check = OfferFacade.get_all_by({"status": OfferStatus.SENT})

        for offer in offers_to_check:
            # Was the offer ever sent?
            if not offer.get("sent_date"):
                continue

            # Was the offer already rejected/accepted by the customer? -> Possibly check status here
            # if ...

            # Check if the maximum possible follow-ups have been exceeded
            if offer.get("follow_up_count") >= MAX_FOLLOWUPS:
                continue

            # Time since the last follow-up or initial sending
            last_time = offer.get("last_follow_up_date") or offer.get("sent_date")
            if last_time < threshold_date:
                # => Follow-up needed
                logger.info(
                    f"Sending follow-up for project: {offer.get('title')} offer number: {offer.get('offer_number')}"
                )

                # Build email
                subject = f"Reminder: Your offer for '{offer.get('title')}', [OFFER#:{offer.get('offer_number')}]"

            body = (
                f"Dear {offer.get('offer_contact_person') or 'Interested Party'},\n\n"
                "I wanted to remind you of my offer. "
                "Do you have any questions or need further information?\n\n"
                "Best regards\n\n"
                "Your Freelancer"
                # Optional: Add GDPR notice
                "\n\n"
                "Hinweis zur Datenverarbeitung gemäß DSGVO:\n"
                "Wir verarbeiten die in dieser E-Mail und in den Angebots- bzw. Projektdaten enthaltenen Informationen ausschließlich zum Zweck der Angebotsanbahnung, -erstellung und gegebenenfalls nachfolgenden Auftragsabwicklung. Dies erfolgt auf Grundlage unserer berechtigten Interessen (Art. 6 Abs. 1 lit. f DSGVO) an der Durchführung vorvertraglicher Maßnahmen sowie – im Falle eines Vertragsschlusses – auf Grundlage der Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO).\n\n"
                "Dabei erheben und speichern wir keine darüber hinausgehenden personenbezogenen Daten; insbesondere werden keine Tracking-Technologien (z. B. zur Ermittlung von Öffnungsraten) eingesetzt. Wir bewahren Ihre Angebots- und Projektdaten nur so lange auf, wie es für die Erfüllung der oben genannten Zwecke oder gesetzliche Aufbewahrungsfristen erforderlich ist.\n\n"
                "Sie haben jederzeit das Recht, der Verarbeitung Ihrer Daten zu widersprechen oder Auskunft über die zu Ihrer Person gespeicherten Daten zu verlangen. Weitere Informationen finden Sie in unserer Datenschutzerklärung [(Link einfügen)].\n\n"
                "\n\n"
                "Notice on data processing according to GDPR:\n"
                "We process the information contained in this email and in the offer or project data exclusively for the purpose of initiating, creating, and possibly subsequent processing of the offer. This is done on the basis of our legitimate interests (Art. 6 para. 1 lit. f GDPR) in carrying out pre-contractual measures and – in the event of a contract conclusion – on the basis of contract fulfillment (Art. 6 para. 1 lit. b GDPR).\n\n"
                "We do not collect or store any additional personal data; in particular, no tracking technologies (e.g., to determine open rates) are used. We retain your offer and project data only as long as necessary for the fulfillment of the aforementioned purposes or legal retention periods.\n\n"
                "You have the right to object to the processing of your data at any time or to request information about the data stored about you. For more information, please refer to our privacy policy [(insert link)].\n\n"
            )

            # Send email
            recipient = offer.get("offer_contact_person_email")
            if not recipient:
                raise ValueError("Missing recpient (contact person email)")
            email_utils.send_email(
                recipient=recipient,
                subject=subject,
                body=body,
            )

            # Update database
            offer["last_follow_up_date"] = now
            offer["follow_up_count"] += 1
            OfferFacade.update(offer.get("id"), offer)

            # Optional: Notify freelancer
            # -> Here an email could be sent to the freelancer,
            #    e.g., "Follow-up has been sent!"

    except Exception as e:
        logger.error(f"Error in send-followups script: {e}")


if __name__ == "__main__":
    main()
