# Database connection setup
from offermee.database.database_manager import DatabaseManager


def connect_to_db():
    # get default database session
    return DatabaseManager.get_default_session
