from openai import OpenAI
from offermee.AI.llm_client import LLMClient


class OpenAIClient(LLMClient):
    def setup_client(self):
        try:
            # Initialize the OpenAI client with the provided API key
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info("OpenAI Client successfully configured.")
        except Exception as e:
            # Log an error message if the client configuration fails
            self.logger.error(f"Error configuring OpenAI: {e}")
            self.client = None

    def extract_to_json(self, prompt: str):
        if not self.client:
            # Log an error message if the client is not initialized
            self.logger.error("The OpenAI client is not initialized.")
            return None
        try:
            # Create a chat completion request to the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            # Return the response as a JSON string
            return response.model_dump_json()
        except Exception as e:
            # Log an error message if the project analysis fails
            self.logger.error(f"Error during extractation: {e}")
            return None
