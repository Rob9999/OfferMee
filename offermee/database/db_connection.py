# Database connection setup
from offermee.database.database_manager import DatabaseManager
from offermee.database.models.freelancer_model import FreelancerModel


def connect_to_db():
    # get default database session
    return DatabaseManager.get_default_session()


def get_freelancer_by_name(name: str):
    try:
        session = connect_to_db()
        return session.query(FreelancerModel).filter_by(name=name).first()
    except Exception as e:
        print(e)
        return None
