# offermee/database/db_connection.py
from contextlib import contextmanager

from offermee.database.database_manager import DatabaseManager
from offermee.database.models.cv_model import CVModel
from offermee.database.models.freelancer_model import FreelancerModel
from offermee.logger import CentralLogger

db_logger = CentralLogger.getLogger("db")


@contextmanager
def session_scope():
    """
    Context manager for database session.

    Ensures that the session is committed on success,
    rolled back on error, and closed afterwards.
    """
    session = connect_to_db()  # Open a new database session
    try:
        yield session  # Provide the session to the context block
        session.commit()  # Commit changes if no exceptions occurred
    except Exception as e:
        session.rollback()  # Roll back changes on error
        db_logger.error(f"Session rollback because of: {e}")
        raise  # Re-raise the exception after rollback
    finally:
        session.close()  # Ensure the session is closed


def connect_to_db():
    """
    Get the default database session from the DatabaseManager.
    """
    return DatabaseManager.get_default_session()


def get_freelancer_by_name(name: str, session=None):
    """
    Retrieve a FreelancerModel instance by name.

    If no session is provided, a new one is created for this query.
    """
    try:
        # Use provided session or create a new one if not given
        session = session or connect_to_db()
        return session.query(FreelancerModel).filter_by(name=name).first()
    except Exception as e:
        db_logger.error(f"Unable to get freelancer by name '{name}': {e}")
        return None


def get_cv_by_freelancer_id(freelancer_id: int, session=None):
    """
    Retrieve a CVModel instance by freelancer_id.

    If no session is provided, a new one is created for this query.
    """
    try:
        # Use provided session or create a new one if not given
        session = session or connect_to_db()
        return session.query(CVModel).filter_by(freelancer_id=freelancer_id).first()
    except Exception as e:
        db_logger.error(f"Unable to get CV by freelancer id '{freelancer_id}': {e}")
        return None
