import datetime
from typing import Any, Dict
from jinja2 import Environment, FileSystemLoader
import os

from offermee.logger import CentralLogger


class OfferGenerator:
    """
    Generator for creating offer documents based on templates.
    """

    def __init__(self, template_dir="templates"):
        """
        Initializes the Jinja2 environment with the specified template directory.

        Args:
            template_dir (str): Directory where the templates are stored.
        """
        self.logger = CentralLogger.getLogger(__name__)
        os.makedirs(template_dir, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_name = "offer_template.html"  # HTML template for offers

    def generate_offer(
        self, project: Dict[str, Any], freelancer: Dict[str, Any], rates: dict
    ):
        """
        Generates an offer based on the project and freelancer data.

        Args:
            project (Dict[str, Any]): The project model with extracted requirements.
            freelancer (Dict[str, Any]): The freelancer model with skills and desired hourly rate.
            rates: The offer rates dictionary containing hourly_rate_remote, hourly_rate_onsite and daily_rate_onsite_pauschal

        Returns:
            str: The generated offer as HTML text.
        """
        try:
            self.logger.info(f"Starting to generate offer ...")
            template = self.env.get_template(self.template_name)
        except Exception as e:
            self.logger.error(f"Error loading the template: {e}")
            return None

        offer = template.render(
            contact_person=(
                project.get("contact_person")
                if project.get("contact_person")
                else "Mr./Ms."  # TODO FIX
            ),
            freelancer=freelancer,
            project=project,
            rates=rates,
            current_date=datetime.datetime.now().strftime("%d.%m.%Y"),
        )
        return offer
