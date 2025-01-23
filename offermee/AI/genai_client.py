from datetime import date
import os
import google.generativeai as genai
from offermee.AI.llm_client import LLMClient


class GenAIClient(LLMClient):
    def setup_client(self):
        try:
            # Configure the generative AI client with the provided API key
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info("Google Generative AI successfully configured.")
        except Exception as e:
            self.logger.error(f"Error configuring Google Generative AI: {e}")
            self.model = None

    def extract_to_json(self, prompt: str):
        if not self.model:
            self.logger.error("The GenerativeModel is not initialized.")
            return None

        self.logger.info("Sending extraction request to genai...")
        # self.logger.debug("Sending prompt:\n" + prompt)
        try:
            # Generate content using the model
            response = self.model.generate_content(
                [
                    {
                        "role": "user",
                        "parts": [prompt],
                    }
                ]
            )
            debug = False
            if debug:
                if response.candidates:
                    self.logger.debug("Received candidates:")
                    for candidate in response.candidates:
                        self.logger.debug(candidate)
                # dump to disk
                dump_path = os.path.join(
                    os.path.expanduser("~"),
                    "offermeedumps",
                    f"response_raw_{date.today().isoformat()}.json",
                )
                with open(dump_path, "w") as f:
                    f.write(str(response))
                self.logger.debug(f"Response dumped to '{dump_path}'")
            json_string = response.candidates[0].content.parts[0].text
            # self.logger.debug("Received JSON:\n" + json_string)
            # Remove the preceding and trailing markdown formatting
            json_string = json_string.strip("```json\n").strip("\n```")
            return json_string
        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            return None
