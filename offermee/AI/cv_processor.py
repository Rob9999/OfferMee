# offermee/cv_processor.py
from datetime import date
import json
import os
from offermee.AI.ai_manager import AIManager
from offermee.utils.config import Config
from offermee.utils.logger import CentralLogger
from offermee.schemas.json.schema_keys import SchemaKey
from offermee.schemas.json.schema_loader import get_schema


class CVProcessor:
    def __init__(self):
        self.logger = CentralLogger.getLogger(__name__)
        self.cv_schema_json = json.dumps(get_schema(SchemaKey.CV), indent=2)
        self.prompt_cv_analyze = (
            "Please analyze the following CV and extract the required information into a structured JSON format.\n"
            "Follow these instructions strictly:\n"
            " 1. For any data that is not available or cannot be evaluated, set its value to null as specified in the schema.\n"
            " 2. Ensure all fields in the JSON schema are filled to the best of your ability.\n"
            " 3. Adhere to the provided JSON schema format without deviations.\n"
            " 4. Normalize dates to one of the following formats: dd.mm.yyyy, mm.yyyy, or yyyy depending on the available precision.\n"
        )

    def analyze_cv(self, cv_text: str) -> dict:
        """
        Sends the CV text to the LLM for analysis and returns the extracted data.
        """
        ai_manager = AIManager().get_default_client()
        if not ai_manager:
            self.logger.error("No AI client available.")
            return {}

        # Prompt mit tatsächlichem CV-Text erstellen
        prompt = (
            self.prompt_cv_analyze
            + f"\n\nSCHEMA:\n{self.cv_schema_json}"
            + f"\n\nCV:\n{cv_text}"
        )

        self.logger.info(f"Send prompt to {ai_manager.model_name}")

        # Anfrage an das LLM senden
        response = ai_manager.extract_to_json(prompt)
        # dump to disk
        dump_path = os.path.join(
            Config.get_instance().get_user_temp_dir(),
            f"response_{date.today().isoformat()}.json",
        )
        with open(dump_path, "w") as f:
            f.write(response)
        self.logger.debug(f"Response dumped to '{dump_path}'")
        try:
            data = json.loads(response)
            self.logger.info("Parsed ai respone to JSON")
            # self.logger.debug(f"Parsed ai respone to JSON:\n{data}")
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error: {e}")
            return {}

    def set_prompt(self, prompt: str):
        self.prompt_cv_analyze = prompt

    @staticmethod
    def get_person_name(json_data: dict, max_firstnames: int = None) -> str:
        """
        Returns a string combining first name(s) and last name based on the specified limit.

        Parameters:
        - json_data: Dictionary containing person data.
        - max_firstnames: Optional integer to limit the number of first names used.
                          - If None, defaults to:
                              * Use only the first first name if multiple are present.
                              * Use all first names if only one is present.
                          - If 0, include no first names, return only the last name.
                          - If >0, include up to that many first names.
                          - If <0, include all available first names.

        Returns:
        - A string with the combined first name(s) and last name.
        """
        person = json_data.get("person", {})
        firstnames = person.get("firstnames", [])
        lastname = person.get("lastname", "")

        # Wenn max_firstnames explizit auf 0 gesetzt ist, Vornamen ignorieren.
        if max_firstnames == 0:
            return lastname.strip()

        # Wenn keine Vornamen vorhanden sind, nur den Nachnamen zurückgeben.
        if not firstnames:
            return lastname.strip()

        # Bestimmen, welche Vornamen verwendet werden sollen
        if isinstance(max_firstnames, int) and max_firstnames > 0:
            selected_firstnames = firstnames[:max_firstnames]
        else:
            selected_firstnames = firstnames

        first_name_part = " ".join(selected_firstnames)
        return (first_name_part + " " + lastname).strip()

    @staticmethod
    def get_all_soft_skills(json_data: dict) -> list:
        """
        Extrahiert und gibt eine Liste aller Soft Skills aus dem JSON zurück.
        Dabei werden Soft Skills aus Projekten und Jobs gesammelt.
        """
        soft_skills_set = set()

        # Durchlaufe alle Projekte und sammle Soft Skills
        projects = json_data.get("projects", [])
        for project_wrapper in projects:
            # Greife auf das verschachtelte 'project'-Objekt zu
            project = project_wrapper.get("project", {})
            skills = project.get("soft-skills", [])
            soft_skills_set.update(skills)

        # Durchlaufe alle Jobs und sammle Soft Skills
        jobs = json_data.get("jobs", [])
        for job_wrapper in jobs:
            # Ähnliche Struktur wie Projekte: Greife auf 'job'-Objekt zu
            job = job_wrapper.get("job", {})
            skills = job.get("soft-skills", [])
            soft_skills_set.update(skills)

        return list(soft_skills_set)

    @staticmethod
    def get_all_tech_skills(json_data: dict) -> list:
        """
        Extrahiert und gibt eine Liste aller Tech Skills aus dem JSON zurück.
        Dabei werden Tech Skills aus Projekten und Jobs gesammelt.
        """
        tech_skills_set = set()

        # Durchlaufe alle Projekte und sammle Tech Skills
        projects = json_data.get("projects", [])
        for project_wrapper in projects:
            # Greife auf das verschachtelte 'project'-Objekt zu
            project = project_wrapper.get("project", {})
            skills = project.get("tech-skills", [])
            tech_skills_set.update(skills)

        # Durchlaufe alle Jobs und sammle Tech Skills
        jobs = json_data.get("jobs", [])
        for job_wrapper in jobs:
            # Ähnliche Struktur wie Projekte: Greife auf 'job'-Objekt zu
            job = job_wrapper.get("job", {})
            skills = job.get("tech-skills", [])
            tech_skills_set.update(skills)

        return list(tech_skills_set)
