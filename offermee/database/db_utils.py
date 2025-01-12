import json
from offermee.database.db_connection import get_cv_by_freelancer_id, session_scope
from offermee.database.models.base_project_model import BaseProjectModel
from offermee.database.models.cv_model import CVModel
from offermee.database.models.enums.project_status import ProjectStatus
from offermee.logger import CentralLogger

db_utils_logger = CentralLogger.getLogger("db_utils")


def load_cv_from_db(freelancer_id: int):
    with session_scope() as session:
        cv: CVModel = get_cv_by_freelancer_id(
            freelancer_id=freelancer_id, session=session
        )
        if not cv:
            return None
        try:
            return json.loads(cv.structured_data)
        except Exception as e1:
            try:
                return json.loads(cv.structured_data.replace("'", '"'))
            except Exception as e2:
                db_utils_logger.log_error(
                    __name__,
                    f"Error parsing JSON CV for freelancer_id #{freelancer_id}: {e1} {e2}",
                )
                return None


def load_projects_from_db(
    project_status: ProjectStatus = ProjectStatus.NEW,
) -> list[BaseProjectModel]:
    with session_scope() as session:
        try:
            projects: list[BaseProjectModel] = (
                session.query(BaseProjectModel)
                .filter(BaseProjectModel.status == project_status)
                .all()
            )
            for project in projects:
                session.expunge(project)
            return projects
        except Exception as e:
            db_utils_logger.log_error(
                __name__,
                f"Error loading projects from db for status {project_status}: {e}",
            )
            return None
