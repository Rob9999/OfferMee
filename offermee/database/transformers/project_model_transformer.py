from datetime import datetime
from dateutil import parser

from offermee.database.models.main_models import ProjectModel, ProjectStatus


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


def json_to_db(json_data) -> ProjectModel:
    """
    Transform JSON data conforming to the Project schema to a ProjectModel instance.
    Assumes json_data is a dict containing a "project" key with the relevant data.
    """
    project_data: dict = json_data.get("project", {})

    # Create a new ProjectModel instance
    project = ProjectModel()
    project.title = project_data.get("title")
    project.description = project_data.get("description")
    project.location = project_data.get("location")

    # Convert lists to comma-separated strings (simple approach)
    project.must_haves = (
        ", ".join(project_data.get("must-have-requirements", []))
        if project_data.get("must-have-requirements")
        else None
    )
    project.nice_to_haves = (
        ", ".join(project_data.get("nice-to-have-requirements", []))
        if project_data.get("nice-to-have-requirements")
        else None
    )
    project.tasks = (
        ", ".join(project_data.get("tasks", [])) if project_data.get("tasks") else None
    )
    project.responsibilities = (
        ", ".join(project_data.get("responsibilities", []))
        if project_data.get("responsibilities")
        else None
    )

    project.hourly_rate = project_data.get("max-hourly-rate")
    project.other_conditions = project_data.get("other-conditions")
    project.contact_person = project_data.get("contact-person")
    project.contact_person_email = project_data.get("contact-person-email")
    project.provider = project_data.get("project-provider")
    project.provider_link = project_data.get("project-provider-link")

    # Parse dates from strings
    project.start_date = parse_date(project_data.get("start-date"))
    project.end_date = parse_date(project_data.get("end-date"))

    project.duration = project_data.get("duration")
    project.extension_option = project_data.get("extension-option")
    project.original_link = project_data.get("original-link")

    return project


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
            "project-provider": project.provider,
            "project-provider-link": project.provider_link,
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
