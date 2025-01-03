from openai import OpenAI
from offermee.AI.llm_client import LLMClient


class OpenAIClient(LLMClient):
    def setup_client(self):
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info("OpenAI Client erfolgreich konfiguriert.")
        except Exception as e:
            self.logger.error(f"Fehler bei der Konfiguration von OpenAI: {e}")
            self.client = None

    def analyze_project(self, project_description: str):

        if not self.client:
            self.logger.error("Der OpenAI client ist nicht initialisiert.")
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": self.make_project_analyze_prompt(
                            project_description
                        ),
                    }
                ],
                temperature=0.2,
                max_tokens=500,
            )
            return response.model_dump_json()
        except Exception as e:
            self.logger.error(f"Fehler bei der Projektanalyse: {e}")
            return None
