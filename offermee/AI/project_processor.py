import json
from offermee.AI.ai_manager import AIManager
from offermee.logger import CentralLogger


class ProjectProcessor:
    def __init__(self):
        self.logger = CentralLogger.getLogger(__name__)
        # prompt and json response format definitions
        self.json_project_format = """
		{ 
			"project":
				{
				"location": "(Remote/On-site/Hybrid)",
				"must-have-requirements": ["requirement1", ...],
				"nice-to-have-requirements": ["requirement1", ...],
				"tasks": ["task1", ...],
				"responsibilities": ["responsibilities1", ...],
				"max-hourly-rate": "rate (if available)",
				"other-conditions": "conditions",
				"contact-person": "contact",
				"project-provider": "provider (if available)",
				"project-provider-link": "link (if available)",
				"start-date": "dd.mm.yyyy (adjust approximate dates to meaningful ones)",
				"original-link": "link"
				}
		}
		"""
        self.prompt_project_analyze = (
            "Please analyze the following project description and extract the following information in a JSON format:\n"
            f"Format: {self.json_project_format}.\n"
            "Please provide the results as a valid JSON object."
        )

    def set_prompt(self, prompt: str):
        self.prompt_project_analyze = prompt

    def analyze_project(self, project_text: str) -> dict:
        """
        Sends the Project text to the LLM for analysis and returns the extracted data.
        """
        ai_manager = AIManager().get_default_client()
        if not ai_manager:
            self.logger.error("No AI client available.")
            return {}

        # Make the prompt with the actual Project text
        prompt = (
            self.prompt_project_analyze + f"\n\nProject Description:\n{project_text}"
        )

        # Send request to the LLM
        response = ai_manager.extract_to_json(prompt)
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error: {e}")
            return {}
