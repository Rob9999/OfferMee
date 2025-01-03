import google.generativeai as genai
from offermee.AI.llm_client import LLMClient


class GenAIClient(LLMClient):
    def setup_client(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info("Google Generative AI erfolgreich konfiguriert.")
        except Exception as e:
            self.logger.error(
                f"Fehler bei der Konfiguration von Google Generative AI: {e}"
            )
            self.model = None

    def analyze_project(self, project_description: str):

        if not self.model:
            self.logger.error("Das GenerativeModel ist nicht initialisiert.")
            return None

        try:
            response = self.model.generate_content(
                [
                    {
                        "role": "user",
                        "parts": [
                            self.make_project_analyze_prompt(
                                project_description=project_description
                            )
                        ],
                    }
                ]
            )
            json_string = response.candidates[0].content.parts[0].text
            # Remove the preceding and trailing markdown formatting
            json_string = json_string.strip("```json\n").strip("\n```")
            return json_string
        except Exception as e:
            self.logger.error(f"Fehler bei der Projektanalyse: {e}")
            return None
