from datetime import datetime
from dateutil import parser

from offermee.database.models.main_models import ProjectModel, ProjectStatus, RFPModel


def parse_date(date_str):
    """
    Parse a date string in dd.mm.yyyy or mm.yyyy format to a datetime.date object.
    Returns None if input is None or cannot be parsed.
    """
    if not date_str:
        return None
    try:
        # Try parsing full date first
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        try:
            # Try parsing month and year
            return datetime.strptime(date_str, "%m.%Y").date()
        except ValueError:
            # Fallback using dateutil for more flexibility
            try:
                return parser.parse(date_str).date()
            except Exception:
                return None


def db_to_json(project: ProjectModel) -> dict:
    """
    Transform a ProjectModel instance to a JSON-like dict conforming to the Project schema.
    """

    # Helper to split comma-separated text back to lists
    def text_to_list(text):
        return [item.strip() for item in text.split(",")] if text else []

    return {
        "project": {
            "title": project.title,
            "description": project.description,
            "location": project.location,
            "must-have-requirements": text_to_list(project.must_haves),
            "nice-to-have-requirements": text_to_list(project.nice_to_haves),
            "tasks": text_to_list(project.workpackages),
            "responsibilities": text_to_list(project.responsibilities),
            "max-hourly-rate": project.hourly_rate,
            "other-conditions": project.other_conditions,
            "contact-person": project.contact_person,
            "provider": project.provider,
            "provider-link": project.provider_link,
            "start-date": (
                project.start_date.strftime("%d.%m.%Y") if project.start_date else None
            ),
            "end-date": (
                project.end_date.strftime("%d.%m.%Y") if project.end_date else None
            ),
            "duration": project.duration,
            "extension-option": project.extension_option,
            "original-link": project.original_link,
        }
    }
