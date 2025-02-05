import traceback
from offermee.database.database_manager import DatabaseManager
from offermee.database.facades.main_facades import RFPFacade
from offermee.logger import CentralLogger


def main():
    try:
        # Load the database with type "TEST" and set shall_overwrite to True
        DatabaseManager.load_database(
            db_type="TEST",
            shall_overwrite=True,
        )
        # Using __name__ to name the logger according to the module name
        logger = CentralLogger.getLogger(__name__)

        # Insert dummy data
        # The data dictionary structure:
        # {
        #     "title": str,
        #     "description": str,
        #     "location": str,
        #     "must_haves": list of str,
        #     "nice_to_haves": list of str,
        #     "tasks": str,
        #     "hourly_rate": float,
        #     "other_conditions": str,
        #     "contact_person": str,
        #     "provider": str,
        #     "original_link": str,
        # }
        dummy_project = RFPFacade.create(
            {
                "title": "Dummy Project",
                "description": "A test project for database functionality.",
                "location": "Remote",
                "must_haves": ["Python", "SQL"],
                "nice_to_haves": ["Docker", "Kubernetes"],
                "tasks": "Develop a database schema and implement it.",
                "hourly_rate": 100.0,
                "other_conditions": "Flexible hours, Agile team.",
                "contact_person": "John Doe",
                "provider": "FreelancerMap",
                "original_link": "https://example.com/project/1",
            }
        )
        logger.info(f"Dummy data was successfully added.\nData:\n{dummy_project}")

        # Read data
        rfps = RFPFacade.get_all()
        for rfp in rfps:
            logger.info(
                f"RFP: {rfp.get('title')}, Description: {rfp.get('description')}"
            )
        logger.info("Test OK.")
    except Exception as error:
        # Log the error with a descriptive message
        logger.error(f"Error during tests: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)


if __name__ == "__main__":
    main()
