import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Basisinstanz als Singleton
class DatabaseManager:
    _instance = None
    Base = declarative_base()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_name="TestDB"):
        if not hasattr(self, "initialized"):  # Verhindert mehrfache Initialisierung
            self.db_name = db_name
            self.engine = create_engine(f"sqlite:///{self.db_name}.db")
            self.Session = sessionmaker(bind=self.engine)
            self.initialized = True  # Markiert als initialisiert

    @staticmethod
    def initialize_database(db_name="TestDB", shall_overwrite=False):
        """
        Erstellt eine neue Datenbank oder überschreibt die vorhandene.
        :param db_name: Name der Datenbank (Standard: TestDB).
        :param shall_overwrite: Überschreibt bestehende Datenbank, falls True.
        """
        db_path = f"{db_name}.db"
        if os.path.exists(db_path) and shall_overwrite:
            os.remove(db_path)
            print(f"Datenbank '{db_path}' wurde überschrieben.")
        elif os.path.exists(db_path):
            print(
                f"Datenbank '{db_path}' existiert bereits und wird nicht überschrieben."
            )
            return

        # Initialisiert Tabellen
        DatabaseManager.Base.metadata.create_all(create_engine(f"sqlite:///{db_path}"))
        print(f"Datenbank '{db_path}' wurde erfolgreich erstellt.")

    @staticmethod
    def backup_database(db_name, backup_path):
        """
        Erstellt eine Sicherung der angegebenen Datenbank.
        :param db_name: Name der zu sichernden Datenbank.
        :param backup_path: Speicherort für die Sicherung.
        """
        db_path = f"{db_name}.db"
        if not os.path.exists(db_path):
            print(f"Fehler: Datenbank '{db_path}' existiert nicht.")
            return

        os.makedirs(backup_path, exist_ok=True)
        backup_file = os.path.join(backup_path, f"{db_name}_backup.db")
        shutil.copy(db_path, backup_file)
        print(f"Datenbank '{db_path}' wurde nach '{backup_file}' gesichert.")
