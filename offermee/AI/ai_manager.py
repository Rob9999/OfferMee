import logging
from offermee.AI.llm_client import LLMClient
from offermee.config import Config

# Import the LLMClient classes
from offermee.AI.openai_client import OpenAIClient
from offermee.AI.genai_client import GenAIClient
from offermee.logger import CentralLogger


class AIManager:
    _instance = None

    def __new__(cls, default_client: str = None):
        if cls._instance is None:
            cls._instance = super(AIManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, default_client: str = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        # Initialize logger
        self.logger = CentralLogger.getLogger(__name__)
        # Initialize a dictionary to store the clients
        self.clients = {}
        self.set_default_client(default_client)
        self._initialized = True

    def set_default_client(self, provider: str):
        """
        Sets the default LLM client for analyzing project descriptions.

        :param provider: Name of the provider (e.g., 'openai', 'genai')
        """
        if not provider:
            self.logger.warning("No default LLM client was set.")
            self.default_client = None
            return

        if provider is None:
            self.logger.warning("No default LLM client was set.")
            self.default_client = None
            return

        provider = provider.lower()

        if provider in ["openai", "genai"]:
            self.logger.debug(
                f"The {provider} client has been set as the default LLM client."
            )
            self.default_client = provider
        else:
            self.logger.error(f"Unknown provider: {provider}")
            raise ValueError(f"Unknown provider: {provider}")

    def get_default_client(self) -> "LLMClient":
        """
        Returns the default LLM client.
        """
        if self.default_client:
            self.logger.debug(
                f"Returning the default LLM client: {self.default_client}"
            )
            return self.get_client(self.default_client)
        else:
            self.logger.error("No default LLM client was set.")
            raise ValueError("No default LLM client was set.")

    def get_client(self, provider: str) -> "LLMClient":
        """
        Returns an instance of the desired LLM client.

        :param provider: Name of the provider (e.g., 'openai', 'genai')
        :return: Instance of an LLMClient
        """
        provider = provider.lower()

        if provider in self.clients:
            self.logger.debug(f"Returning the already initialized {provider} client.")
            return self.clients[provider]

        if provider == "openai":
            client = OpenAIClient(
                api_key=Config.get_ai_family_api_key("openai"),
                model_name=Config.get_ai_family_model("openai"),
            )
            self.clients[provider] = client
            self.logger.info("OpenAI Client created and stored.")
            return client

        elif provider == "genai":
            client = GenAIClient(
                api_key=Config.get_ai_family_api_key("genai"),
                model_name=Config.get_ai_family_model("genai"),
            )
            self.clients[provider] = client
            self.logger.info("GenAI Client created and stored.")
            return client

        else:
            self.logger.error(f"Unknown provider: {provider}")
            raise ValueError(f"Unknown provider: {provider}")
