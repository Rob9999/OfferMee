from offermee.database.database_manager import DatabaseManager
from offermee.database.facades.main_facades import ProjectFacade
from offermee.logger import CentralLogger


def main():
    # select database type
    db_manager = DatabaseManager.load_database("TEST", shall_overwrite=True)
    logger = CentralLogger.getLogger(__name__)

    try:
        # Dummy-Daten einfügen
        dummy_project = ProjectFacade.create(
            {
                "title": "Dummy Project",
                "description": "A test project for database functionality.",
                "location=": "Remote",
                "must_haves": "Python, SQL",
                "nice_to_haves": "Docker, Kubernetes",
                "tasks": "Develop a database schema and implement it.",
                "hourly_rate": 100.0,
                "other_conditions": "Flexible hours, Agile team.",
                "contact_person": "John Doe",
                "provider": "FreelancerMap",
                "original_link": "https://example.com/project/1",
            }
        )
        logger.info("Dummy-Daten wurden erfolgreich hinzugefügt.")

        # Daten auslesen
        projects = ProjectFacade.get_all()
        for project in projects:
            logger.info(
                f"Projekt: {project.title}, Beschreibung: {project.description}"
            )
        logger.info("Test OK.")
    except Exception as e:
        logger.error(f"Fehler während der Tests: {e}")


if __name__ == "__main__":
    main()
