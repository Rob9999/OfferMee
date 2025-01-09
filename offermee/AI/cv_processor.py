# offermee/cv_processor.py
import json
from offermee.AI.ai_manager import AIManager
from offermee.logger import CentralLogger


class CVProcessor:
    def __init__(self):
        self.logger = CentralLogger.getLogger(__name__)
        # Prompt und JSON-Formatdefinitions-Strings ...
        self.json_project_format: str = """
        { 
            "project":
                {
                "title": "title",
                "start": "dd.mm.yyyy or mm.yyyy",
                "end": "dd.mm.yyyy or mm.yyyy",
                "person-days": "number",
                "industry": "industry",
                "firm": "firm",
                "result": "result",
                "tasks": ["task1", ...],
                "soft-skills": ["skill1", ...],
                "tech-skills": ["skill1", ...],
                "responsibilities": ["resp1", ...]
            }
        }
        """
        self.json_job_format: str = """
        { 
            "job":
                {
                "title": "title",
                "start": "dd.mm.yyyy or mm.yyyy",
                "end": "dd.mm.yyyy or mm.yyyy",
                "person-days": "number",
                "industry": "industry",
                "firm": "firm",
                "result": "result",
                "tasks": ["task1", ...],
                "soft-skills": ["skill1", ...],
                "tech-skills": ["skill1", ...],
                "responsibilities": ["resp1", ...]
            }
        }
        """
        self.json_education_format: str = """
        { 
            "education":
                {
                "title": "title",
                "start": "dd.mm.yyyy or mm.yyyy",
                "end": "dd.mm.yyyy or mm.yyyy",
                "person-days": "number",
                "facility": "facility",
                "type": "Master/Fachhochschule/Technische Hochschule/Bachelor/PhD/Highschool/Primaryschool/Online/Bootcamp",
                "grade": "MA/BA/Diplom-Ingenieur/Diplom-Ingenieur (FH)/Diplom-Ingenieur (TH)/PhD/Highschool/Primaryschool/Certificate/etc",
                "topics": ["topic1", ...]
            }
        }
        """
        self.json_person_format: str = """
        { 
            "person":
                {
                "firstnames": ["firstname1", ...],
                "lastname": "lastname",
                "birth": "dd.mm.yyyy",
                "birth-place": "birth-place",
                "address": "address",
                "city": "city",                
                "zip-code": "zip-code",
                "country": "country",
                "phone": "phone",   
                "email": "email",
                "linkedin": "linkedin",
                "xing": "xing",
                "github": "github",
                "website": "website",
                "languages": ["language1", ...]
            }
        }
        """
        self.json_contact_format: str = """
        { 
            "contact":
                {   
                "address": "address",
                "city": "city",
                "zip-code": "zip-code",
                "country": "country",                                 
                "phone": "phone",   
                "email": "email",
                "linkedin": "linkedin",
                "xing": "xing",
                "github": "github",
                "website": "website"
            }
        }
        """

        self.json_tech_skills_format: str = """
        { 
            "skill":
                {   
                "name": "name",
                "month": "month (month of evaluatable experiences)",
                "experience": "(0....10) (if evaluatable)",
            }
        }
        """

        self.json_soft_skills_format: str = """
        { 
            "skill":
                {   
                "name": "name",
                "month": "month (month of evaluatable experiences)",
                "experience": "(0....10) (if evaluatable)",
            }
        }
        """

        self.prompt_cv_analyze = (
            "Please analyze the following CV and extract the following information in a JSON format:\n"
            f"1. projects: Format [{self.json_project_format}].\n"
            f"2. jobs: Format [{self.json_job_format}].\n"
            f"3. educations: Format [{self.json_education_format}].\n"
            f"4. person: Format {self.json_person_format}.\n"
            f"5. contact: Format {self.json_contact_format}.\n"
            # f"6. soft-skills: Format {self.json_soft_skills_format}"
            # f"7. tech-skills: Format {self.json_tech_skills_format}"
            "Please provide the results as a valid JSON object."
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
        prompt = self.prompt_cv_analyze + f"\n\nCV:\n{cv_text}"

        self.logger.info(f"Send prompt to {ai_manager.model_name}")

        # Anfrage an das LLM senden
        response = ai_manager.extract_to_json(prompt)
        self.logger.info(f"Response {response}")
        try:
            data = json.loads(response)
            self.logger.info("Parsed ai respone to JSON")
            self.logger.info(f"Parsed ai respone to JSON:\n{data}")
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
        for project in projects:
            skills = project.get("soft-skills", [])
            soft_skills_set.update(skills)

        # Durchlaufe alle Jobs und sammle Soft Skills
        jobs = json_data.get("jobs", [])
        for job in jobs:
            skills = job.get("soft-skills", [])
            soft_skills_set.update(skills)

        # Optional: Weitere Bereiche wie "person" oder "contact" hinzufügen, falls benötigt.

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
        for project in projects:
            skills = project.get("tech-skills", [])
            tech_skills_set.update(skills)

        # Durchlaufe alle Jobs und sammle Tech Skills
        jobs = json_data.get("jobs", [])
        for job in jobs:
            skills = job.get("tech-skills", [])
            tech_skills_set.update(skills)

        # Optional: Weitere Bereiche wie "skill" auf oberster Ebene hinzufügen, falls benötigt.

        return list(tech_skills_set)
