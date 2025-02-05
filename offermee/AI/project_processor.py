import json
from offermee.AI.ai_manager import AIManager
from offermee.logger import CentralLogger
from offermee.schemas.json.schema_keys import SchemaKey
from offermee.schemas.json.schema_loader import get_schema


class RFPProcessor:
    def __init__(self):
        self.logger = CentralLogger.getLogger(__name__)
        # prompt and json response format definitions
        self.project_schema_json = json.dumps(get_schema(SchemaKey.PROJECT), indent=2)
        self.prompt_project_analyze = (
            "Please analyze the following project description and extract the required information into a structured JSON format.\n"
            "Follow these instructions strictly:\n"
            " 1. For any data that is not available or cannot be evaluated, set its value to null as specified in the schema.\n"
            " 2. Ensure all fields in the JSON schema are filled to the best of your ability.\n"
            " 3. Adhere to the provided JSON schema format without deviations.\n"
            " 4. Normalize dates to one of the following formats: dd.mm.yyyy, mm.yyyy, or yyyy depending on the available precision.\n"
        )

    def set_prompt(self, prompt: str):
        self.prompt_project_analyze = prompt

    def analyze_rfp(self, project_text: str) -> dict:
        """
        Sends the Project text to the LLM for analysis and returns the extracted data.
        """
        ai_manager = AIManager().get_default_client()
        if not ai_manager:
            self.logger.error("No AI client available.")
            return {}

        # Make the prompt with the actual Project text
        prompt = (
            self.prompt_project_analyze
            + f"\n\nSCHEMA:\n{self.project_schema_json}"
            + f"\n\nPROJECT DESCRIPTION:\n{project_text}"
        )

        # Send request to the LLM
        response = ai_manager.extract_to_json(prompt)
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error: {e}")
            return {}
