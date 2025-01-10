# Database connection setup
from offermee.database.database_manager import DatabaseManager
from offermee.database.models.cv_model import CVModel
from offermee.database.models.freelancer_model import FreelancerModel
from offermee.logger import CentralLogger

db_logger = CentralLogger.getLogger("db")


def connect_to_db():
    # get default database session
    return DatabaseManager.get_default_session()


def get_freelancer_by_name(name: str):
    try:
        session = connect_to_db()
        return session.query(FreelancerModel).filter_by(name=name).first()
    except Exception as e:
        db_logger.error(f"Unable to get freelancer by name {name}: {e}")
        return None


def get_cv_by_freelancer_id(freelancer_id):
    try:
        session = connect_to_db()
        return session.query(CVModel).filter_by(freelancer_id=freelancer_id).first()
    except Exception as e:
        db_logger.error(f"Unable to get cv by freelancer id {freelancer_id}: {e}")
        return None
