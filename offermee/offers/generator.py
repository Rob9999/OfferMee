import datetime
from typing import Any, Dict
from jinja2 import Environment, BaseLoader
from babel import dates, numbers

from offermee.utils.logger import CentralLogger
from offermee.utils.international import _T  # Übersetzungen einbinden


class OfferGenerator:
    """
    Generator for creating internationalized offer documents based on templates.
    """

    def __init__(self):
        """
        Initializes the OfferGenerator.
        """
        self.logger = CentralLogger.getLogger(__name__)
        self.env = Environment(loader=BaseLoader())  # Templates kommen als Strings

    def generate_html_offer(
        self,
        html_template: str,
        rfp: Dict[str, Any],
        freelancer: Dict[str, Any],
        rates: Dict[str, float],
        language: str = "en",
        currency: str = "EUR",
    ) -> str:
        """
        Renders an internationalized HTML offer using the provided template and data.

        :param html_template: The HTML template as a string.
        :param rfp: Dictionary containing project details (Request For Proposal).
        :param freelancer: Dictionary containing freelancer details.
        :param rates: Dictionary containing rate information as floats.
        :param language: Language code for localization (e.g., "de", "en").
        :param currency: Currency code for rates (e.g., "USD", "EUR").
        :return: Rendered HTML string or None in case of an error.
        """
        try:
            self.logger.info("Starting to generate offer...")
            template = self.env.from_string(html_template)
        except Exception as e:
            self.logger.error(f"Error parsing the template: {e}")
            return None

        try:
            # Lokalisierung vorbereiten
            current_date = dates.format_date(
                datetime.datetime.now(), format="long", locale=language
            )
            formatted_rates = {
                key: numbers.format_currency(value, currency, locale=language)
                for key, value in rates.items()
            }

            # Template rendern
            offer = template.render(
                contact_person=rfp.get("contact_person", _T("Mr./Ms.")),
                freelancer=freelancer,
                project=rfp,
                rates=formatted_rates,
                current_date=current_date,
            )
            self.logger.info("Offer successfully generated.")
            return offer
        except Exception as e:
            self.logger.error(f"Error rendering the template: {e}")
            return None
