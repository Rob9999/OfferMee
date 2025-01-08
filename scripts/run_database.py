from offermee.database.database_manager import DatabaseManager
from offermee.database.models.base_project_model import BaseProjectModel
from offermee.database.models.edited_project_model import EditedProjectModel
from offermee.database.models.intermediate_project_model import IntermediateProjectModel
from offermee.database.models.matching_score_model import MatchingScoreModel
from offermee.logger import CentralLogger


def main():
    # select database type
    db_manager = DatabaseManager("TEST", shall_overwrite=True)
    # start session
    session = db_manager.Session()

    try:
        # Dummy-Daten einfügen
        dummy_project = BaseProjectModel(
            title="Dummy Project",
            description="A test project for database functionality.",
            location="Remote",
            must_haves="Python, SQL",
            nice_to_haves="Docker, Kubernetes",
            tasks="Develop a database schema and implement it.",
            hourly_rate=100.0,
            other_conditions="Flexible hours, Agile team.",
            contact_person="John Doe",
            provider="FreelancerMap",
            original_link="https://example.com/project/1",
        )
        session.add(dummy_project)
        session.commit()
        print("Dummy-Daten wurden erfolgreich hinzugefügt.")

        # Daten auslesen
        projects = session.query(BaseProjectModel).all()
        for project in projects:
            print(f"Projekt: {project.title}, Beschreibung: {project.description}")

    except Exception as e:
        print(f"Fehler während der Tests: {e}")
    finally:
        session.close()
        print("Datenbank-Session geschlossen.")


if __name__ == "__main__":
    main()
