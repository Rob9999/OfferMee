import datetime
from jinja2 import Environment, FileSystemLoader
import os


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
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_name = "offer_template.html"  # HTML template for offers

    def generate_offer(self, project, freelancer):
        """
        Generates an offer based on the project and freelancer data.

        Args:
            project (BaseProjectModel): The project model with extracted requirements.
            freelancer (FreelancerModel): The freelancer model with skills and desired hourly rate.

        Returns:
            str: The generated offer as HTML text.
        """
        try:
            template = self.env.get_template(self.template_name)
        except Exception as e:
            print(f"Error loading the template: {e}")
            return None

        offer = template.render(
            contact_person=(
                project.contact_person if project.contact_person else "Mr./Ms."
            ),
            freelancer=freelancer,
            project=project,
            current_date=datetime.datetime.now().strftime("%d.%m.%Y"),
        )
        return offer
