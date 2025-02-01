import datetime
import json
import locale
from typing import Any, Dict
from dateutil import parser
import os
import logging
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from offermee.config import Config
from offermee.database.transformers.to_json_schema import (
    build_full_json_schema,
    db_model_to_json_schema,
)
from offermee.logger import CentralLogger


class DatabaseManager:
    _data_base_instance: "DatabaseManager._DataBase" = None
    Base = declarative_base()
    db_selectable = {"TEST": "test_offermee", "PROD": "offermee"}
    db_type = "TEST"

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
        if DatabaseManager.db_type != db_type:
            DatabaseManager.db_type = db_type
            logging.info(f"Default database set to: {db_type}")
            DatabaseManager._reload_database()
        return db_type

    @staticmethod
    def _reload_database():
        logging.info(f"Reloading database type: {DatabaseManager.db_type} ...")
        DatabaseManager._data_base_instance = DatabaseManager._DataBase(
            DatabaseManager.db_type
        )
        logging.info(f"Database reloaded type: {DatabaseManager.db_type}")

    @staticmethod
    def load_database(db_type="TEST", shall_overwrite=False):
        logging.info(f"Loading database type: {db_type} ...")
        DatabaseManager.db_type = DatabaseManager.validate_db_type(db_type)
        DatabaseManager._data_base_instance = DatabaseManager._DataBase(
            DatabaseManager.db_type, shall_overwrite=shall_overwrite
        )
        logging.info(f"Database loaded type: {DatabaseManager.db_type}")

    @staticmethod
    def get_default_session() -> Session:
        if not DatabaseManager._data_base_instance:
            DatabaseManager._data_base_instance = DatabaseManager._DataBase(
                DatabaseManager.db_type
            )
        return DatabaseManager._data_base_instance.session_maker()

    @staticmethod
    def get_db_path(db_type="TEST") -> str:
        db_type = DatabaseManager.validate_db_type(db_type)
        db_dir = Config.get_instance().get_central_db_dir()
        return f"{db_dir}/{DatabaseManager.db_selectable[db_type]}.db"

    class _DataBase:
        session_maker: sessionmaker = None

        def __init__(
            self,
            db_type: str = "TEST",
            create_all_tables: bool = True,
            shall_overwrite: bool = False,
        ):
            if not hasattr(self, "initialized"):  # Verhindert mehrfache Initialisierung
                self.logger = CentralLogger.getLogger(__name__)
                self.session_maker, self.engine, self.db_path, self.db_type = (
                    self._initialize_database(
                        db_type=db_type,
                        create_all_tables=create_all_tables,
                        shall_overwrite=shall_overwrite,
                    )
                )
                self.initialized = True  # Markiert als initialisiert
                self.logger.info(f"Database initialized with db_type: {db_type}")

        def _initialize_database(
            self,
            db_type: str = "TEST",
            create_all_tables: bool = True,
            shall_overwrite: bool = False,
        ) -> tuple[sessionmaker, Engine, str, str]:
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
                self._delete_database(db_type)
            db_path = DatabaseManager.get_db_path(db_type)
            engine = self._create_database(db_path, create_all_tables=create_all_tables)
            session_maker: sessionmaker = sessionmaker(bind=engine)
            logging.info(f"Database {db_type} initialized at {db_path}")
            return session_maker, engine, db_path, db_type

        def _store_all_db_models_as_json_schema(self, full: bool = False):
            storage_dir = os.path.normpath(
                "./offermee/schemas/json/db" + ("/full" if full else "")
            )
            os.makedirs(storage_dir, exist_ok=True)
            logging.info(f"Storing all db models as json schema to '{storage_dir}' ...")
            try:
                # Iteriere über alle Mapper (Klassen), die in Base registriert sind
                for mapper in DatabaseManager.Base.registry.mappers:
                    model_cls = mapper.class_

                    # Generiere ein JSON-Schema
                    schema_dict: Dict[str, Any] = (
                        build_full_json_schema(model=model_cls)
                        if full
                        else db_model_to_json_schema(model=model_cls)
                    )
                    # logging.debug(
                    #    f"Generated JSON schema from db model '{model_cls.__name__}':\n{schema_dict}"
                    # )

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
                logging.error(f"Error storing all DB schemas: {e}", exc_info=True)

        def _delete_database(self, db_type: str):
            db_type = DatabaseManager.validate_db_type(db_type)
            if db_type == "PROD":  # deny overwriting production database
                logging.error(f"Deleting production database is not allowed: {db_path}")
                raise ValueError(
                    f"Deleting production database is not allowed: {db_path}"
                )
            db_path = DatabaseManager.get_db_path(db_type)
            if os.path.exists(db_path):
                if db_path != DatabaseManager.get_db_path("PROD"):
                    os.remove(db_path)
                    logging.info(f"Deleted existing database: {db_path}")

        def _create_database(self, db_path: str, create_all_tables: bool = False):
            if os.path.exists(db_path) and not create_all_tables:
                logging.info(
                    f"Database already exists at {db_path}. Skipping table creation."
                )
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
            # store all db tables as json schema
            self._store_all_db_models_as_json_schema()
            self._store_all_db_models_as_json_schema(full=True)
            return engine
