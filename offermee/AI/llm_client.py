import openai
from offermee.config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIClient:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL

    def analyze_project(self, project_description):
        """
        Schlüsselt die Projektbeschreibung nach Standards auf.
        """
        prompt = (
            "Please analyze the following project description and extract the following information:\n"
            "1. Location (Remote/On-site/Hybrid).\n"
            "2. Must-Have Requirements.\n"
            "3. Nice-To-Have Requirements.\n"
            "4. Tasks/Responsibilities.\n"
            "5. Max Hourly Rate (if provided).\n"
            "6. Other conditions.\n"
            "7. Contact Person (if provided).\n"
            "8. Project Provider.\n"
            "9. Project Start Date.\n"
            "10. Original Link.\n\n"
            f"Project Description:\n{project_description}\n\n"
            "Return the result as a JSON object."
        )

        try:
            response = openai.ChatCompletion.create(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message["content"]
        except openai.error.RateLimitError:
            print("Rate Limit überschritten. Bitte versuchen Sie es später erneut.")
        except openai.error.AuthenticationError:
            print("Authentifizierungsfehler. Überprüfen Sie Ihren API-Schlüssel.")
        except openai.error.OpenAIError as e:
            print(f"Error communicating with OpenAI: {e}")
            return None
