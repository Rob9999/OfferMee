from jinja2 import Template


class OfferGenerator:

    @staticmethod
    def generate_offer(project, freelancer):
        """
        Generiert ein Angebot basierend auf dem Projekt und den Freelancer-Daten.

        Args:
            project (BaseProjectModel): Das Projektmodell mit extrahierten Anforderungen.
            freelancer (FreelancerModel): Das Freelancer-Modell mit Fähigkeiten und gewünschtem Stundensatz.

        Returns:
            str: Das generierte Angebot als Text.
        """
        template_str = """
        Sehr geehrte/r {{ contact_person }},

        vielen Dank für Ihr Interesse an meinen Dienstleistungen als {{ freelancer.name }}.

        Basierend auf Ihrer Projektbeschreibung "{{ project.title }}" biete ich Ihnen folgendes an:

        - **Beschreibung:** {{ project.description }}
        - **Stundensatz:** {{ freelancer.desired_rate }} €/Stunde
        - **Startdatum:** {{ project.start_date }}
        - **Weitere Bedingungen:** {{ project.other_conditions }}

        Ich freue mich auf eine erfolgreiche Zusammenarbeit.

        Mit freundlichen Grüßen,
        {{ freelancer.name }}
        """
        template = Template(template_str)
        offer = template.render(
            contact_person=(
                project.contact_person if project.contact_person else "Herr/Frau"
            ),
            freelancer=freelancer,
            project=project,
        )
        return offer
