import datetime
import json
import locale
from typing import Any, Dict
from dateutil import parser
import os
import logging
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from offermee.config import Config
from offermee.database.transformers.to_json_schema import db_model_to_json_schema
from offermee.logger import CentralLogger


"""
DatabaseManager is a singleton class that manages the database connection and operations.
Attributes:
    _instance (DatabaseManager): Singleton instance of the DatabaseManager.
    Base (declarative_base): SQLAlchemy base class for declarative class definitions.
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
    db_selectable = {"TEST": "test_offermee", "PROD": "offermee"}
    db_selected = "TEST"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            logging.info("Creating a new instance of DatabaseManager")
        return cls._instance

    def __init__(self, db_type="TEST", shall_overwrite=False):
        if not hasattr(self, "initialized"):  # Verhindert mehrfache Initialisierung
            self.logger = CentralLogger.getLogger(__name__)
            self.Session, self.engine, self.db_path = (
                DatabaseManager._initialize_database(
                    db_type=db_type,
                    create_all_tables=True,  # create all tables (run a 'hello_all_new_tables = DatabaseManager(db_type=YOURCHOICE)', to get all new tables)
                    shall_overwrite=shall_overwrite,
                )
            )
            self.db_type = DatabaseManager.set_default_db(db_type)
            self.initialized = True  # Markiert als initialisiert
            self.logger.info(f"DatabaseManager initialized with db_type: {db_type}")

    @staticmethod
    def get_instance():
        return DatabaseManager._instance

    @staticmethod
    def parse_date(date_str: str, locale_str: str = "de_DE.UTF-8") -> datetime.date:
        if date_str is None:
            return None

        # Set locale for date parsing
        try:
            locale.setlocale(locale.LC_TIME, locale_str)
        except locale.Error:
            raise ValueError(f"Locale {locale_str} not supported on this system")

        # Try parsing with dateutil.parser
        try:
            return parser.parse(date_str).date()
        except (ValueError, TypeError):
            pass

        # Reset locale to default
        locale.setlocale(locale.LC_TIME, "")

        date_formats = ["%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]
        for date_format in date_formats:
            try:
                return datetime.datetime.strptime(date_str, date_format).date()
            except ValueError:
                continue

        raise ValueError(
            "Incorrect date format, should be one of YYYY-MM-DD, DD-MM-YYYY, DD.MM.YYYY, MM/DD/YYYY, or DD/MM/YYYY"
        )

    @staticmethod
    def join_list(value, delimiter=", "):
        if value is None:
            return None
        if not isinstance(value, list):
            value = [value]
        return delimiter.join(value)

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
        session, engine, db_path = DatabaseManager._initialize_database(
            DatabaseManager.db_selected, create_all_tables=False, shall_overwrite=False
        )
        return session

    @staticmethod
    def get_db_path(db_type="TEST") -> str:
        db_type = DatabaseManager.validate_db_type(db_type)
        db_dir = Config.get_instance().get_central_db_dir()
        return f"{db_dir}/{DatabaseManager.db_selectable[db_type]}.db"

    @staticmethod
    def _initialize_database(
        db_type: str = "TEST",
        create_all_tables: bool = False,
        shall_overwrite: bool = False,
    ) -> tuple[sessionmaker, Engine, str]:
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
        engine = DatabaseManager._create_database(
            db_path, create_all_tables=create_all_tables
        )
        DatabaseManager._store_all_db_models_as_json_schema()
        session = sessionmaker(bind=engine)()
        logging.info(f"Database {db_type} initialized at {db_path}")
        return session, engine, db_path

    @staticmethod
    def _store_all_db_models_as_json_schema():
        storage_dir = os.path.normpath("../schemas/json/db")
        os.makedirs(storage_dir, exist_ok=True)
        logging.info(f"Storing all db models as json schema to '{storage_dir}' ...")
        try:
            # Iteriere über alle Mapper (Klassen), die in Base registriert sind
            for mapper in DatabaseManager.Base.registry.mappers:
                model_cls = mapper.class_

                # Generiere ein JSON-Schema
                schema_dict: Dict[str, Any] = db_model_to_json_schema(model=model_cls)

                # JSON als String serialisieren
                json_schema_str = json.dumps(schema_dict, indent=4)

                # Dateiname = <ModelName>.schema.json
                filename = f"{model_cls.__name__}.schema.json"
                filepath = os.path.join(storage_dir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(json_schema_str)

                logging.info(
                    f"Created schema file for model {model_cls.__name__} -> {filepath}"
                )

        except Exception as e:
            logging.error("Error storing all DB schemas", exc_info=True)

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
    def _create_database(db_path: str, create_all_tables: bool = False):
        if os.path.exists(db_path) and not create_all_tables:
            logging.info(f"Database already exists at {db_path}. Skipping creation.")
            # Connect to the existing database
            engine = create_engine(f"sqlite:///{db_path}")
            return engine
        # Create new database if it doesn't exist or create tables if specified so
        # Ensure the directory exists
        directory = os.path.dirname(db_path)
        os.makedirs(directory, exist_ok=True)
        # create db
        engine = create_engine(f"sqlite:///{db_path}")
        # create all tables
        DatabaseManager.Base.metadata.create_all(engine)
        logging.info(f"Database created at {db_path}")
        return engine
