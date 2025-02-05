# offermee/database/db_connection.py
from contextlib import contextmanager

from offermee.database.database_manager import DatabaseManager
from offermee.utils.logger import CentralLogger
from sqlalchemy.orm import Session

db_logger = CentralLogger.getLogger("db")


@contextmanager
def session_scope():
    """
    Context manager for database session.

    Ensures that the session is committed on success,
    rolled back on error, and closed afterwards.
    """
    session: Session = connect_to_db()  # Open a new database session
    try:
        yield session  # Provide the session to the context block
        session.commit()  # Commit changes if no exceptions occurred
    except Exception as e:
        session.rollback()  # Roll back changes on error
        db_logger.error(f"Session rollback because of: {e}")
        raise  # Re-raise the exception after rollback
    finally:
        session.close()  # Ensure the session is closed


def connect_to_db() -> Session:
    """
    Get the default database session from the DatabaseManager.
    """
    return DatabaseManager.get_default_session()
