import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging


"""
DatabaseManager is a singleton class that manages the database connection and operations.
Attributes:
    _instance (DatabaseManager): Singleton instance of the DatabaseManager.
    Base (declarative_base): SQLAlchemy base class for declarative class definitions.
    db_dir (str): Directory where the database files are stored.
    db_selectable (dict): Dictionary mapping environment types to database names.
    db_selected (str): Currently selected database type.
Methods:
    __new__(cls, *args, **kwargs): Creates a new instance of DatabaseManager if it doesn't exist.
    __init__(self, db_type="TEST", shall_overwrite=True): Initializes the DatabaseManager with the specified database type.
    validate_db_type(db_type="TEST") -> str: Validates the provided database type.
    set_default_db(db_type="TEST") -> str: Sets the default database type.
    get_default_session() -> sessionmaker: Returns a sessionmaker for the default database.
    get_db_path(db_type="TEST") -> str: Returns the file path for the specified database type.
    _initialize_database(db_type="TEST", shall_overwrite=False) -> sessionmaker: Initializes a new database or overwrites the existing one.
    _delete_database(db_type: str): Deletes the specified database if it exists.
    _create_database(db_path: str): Creates a new database at the specified path.
"""


class DatabaseManager:
    _instance = None
    Base = declarative_base()
    db_dir = "dbs"
    db_selectable = {"TEST": "test_offermee", "PROD": "offermee"}
    db_selected = "TEST"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            logging.info("Creating a new instance of DatabaseManager")
        return cls._instance

    def __init__(self, db_type="TEST", shall_overwrite=True):
        if not hasattr(self, "initialized"):  # Verhindert mehrfache Initialisierung
            self.logger = logging.getLogger(__name__)
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
            )
            self.db_type = DatabaseManager.set_default_db(db_type)
            if shall_overwrite:
                DatabaseManager._delete_database(db_type)
            self.db_path = DatabaseManager.get_db_path(db_type)
            self.engine = DatabaseManager._create_database(self.db_path)
            self.Session = sessionmaker(bind=self.engine)
            self.initialized = True  # Markiert als initialisiert
            self.logger.info(f"DatabaseManager initialized with db_type: {db_type}")

    @staticmethod
    def validate_db_type(db_type="TEST") -> str:
        if db_type not in DatabaseManager.db_selectable:
            logging.error(f"Unknown db_type: {db_type}")
            raise ValueError(f"Unknown db_type: {db_type}")
        logging.info(f"validated successfully db_type: {db_type}")
        return db_type

    @staticmethod
    def set_default_db(db_type="TEST") -> str:
        db_type = DatabaseManager.validate_db_type(db_type)
        DatabaseManager.db_selected = db_type
        logging.info(f"Default database set to: {db_type}")
        return db_type

    @staticmethod
    def get_default_session() -> sessionmaker:
        return DatabaseManager._initialize_database(
            DatabaseManager.db_selected, shall_overwrite=False
        )()

    @staticmethod
    def get_db_path(db_type="TEST") -> str:
        db_type = DatabaseManager.validate_db_type(db_type)
        if not os.path.exists(DatabaseManager.db_dir):
            os.makedirs(DatabaseManager.db_dir)
            logging.info(f"Created directory: {DatabaseManager.db_dir}")
        return f"{DatabaseManager.db_dir}/{DatabaseManager.db_selectable[db_type]}.db"

    @staticmethod
    def _initialize_database(db_type="TEST", shall_overwrite=False) -> sessionmaker:
        """
        Creates a new database or overwrites the existing one.
        :param db_type: Name of the database (default: TEST).
        :param shall_overwrite: Overwrites the existing database if True.
        :return: A sessionmaker bound to the created database.
        """
        logging.info(
            f"Initializing database: {db_type}, shall_overwrite: {shall_overwrite}"
        )
        if shall_overwrite:
            DatabaseManager._delete_database(db_type)
        db_path = DatabaseManager.get_db_path(db_type)
        engine = DatabaseManager._create_database(db_path)
        session = sessionmaker(bind=engine)
        logging.info(f"Database {db_type} initialized at {db_path}")
        return session

    @staticmethod
    def _delete_database(db_type: str):
        db_type = DatabaseManager.validate_db_type(db_type)
        if db_type == "PROD":  # deny overwriting production database
            logging.error(f"Deleting production database is not allowed: {db_path}")
            raise ValueError(f"Deleting production database is not allowed: {db_path}")
        db_path = DatabaseManager.get_db_path(db_type)
        if os.path.exists(db_path):
            if db_path != DatabaseManager.get_db_path("PROD"):
                os.remove(db_path)
                logging.info(f"Deleted existing database: {db_path}")

    @staticmethod
    def _create_database(db_path: str):
        engine = create_engine(f"sqlite:///{db_path}")
        DatabaseManager.Base.metadata.create_all(engine)
        logging.info(f"Database created at {db_path}")
        return engine
