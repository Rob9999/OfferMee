import logging
from offermee.AI.llm_client import LLMClient

# Import the LLMClient classes
from offermee.AI.openai_client import OpenAIClient
from offermee.AI.genai_client import GenAIClient
from offermee.utils.logger import CentralLogger


class AIManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        # Initialize logger
        self.logger = CentralLogger.getLogger(__name__)
        # Initialize a dictionary to store the clients
        self.clients = {}
        self.default_client = None
        self.default_client_data = None
        self._initialized = True

    def set_default_client(self, provider: str = None, data: dict = None):
        """
        Sets the default LLM client for analyzing project descriptions.

        :param provider: Name of the provider (e.g., 'openai', 'genai')
        :param data: Dictionary with the necessary data for the client
        """
        if not provider:
            self.logger.warning("No default LLM client was set.")
            self.default_client = None
            self.default_client_data = None
            return

        if provider is None:
            self.logger.warning("No default LLM client was set.")
            self.default_client = None
            self.default_client_data = None
            return

        provider = provider.lower()

        if provider in ["openai", "genai"]:
            self.default_client = provider
            self.default_client_data = data
            self.logger.info(f"Set the default client to: {provider}")
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
            return self.get_client(self.default_client, self.default_client_data)
        else:
            self.logger.error("No default LLM client was set.")
            raise ValueError("No default LLM client was set.")

    def get_client(self, provider: str, data: dict) -> "LLMClient":
        """
        Returns an instance of the desired LLM client.

        :param provider: Name of the provider (e.g., 'openai', 'genai')
        :param data: Dictionary with the necessary data for the client
        :return: Instance of an LLMClient
        """
        provider = provider.lower()

        if provider in self.clients:
            self.logger.debug(f"Returning the already initialized {provider} client.")
            return self.clients[provider]

        if provider == "openai":
            client = OpenAIClient(
                api_key=data.get("api_key"),
                model_name=data.get("model"),
            )
            self.clients[provider] = client
            self.logger.info("OpenAI Client created and stored.")
            return client

        elif provider == "genai":
            client = GenAIClient(
                api_key=data.get("api_key"),
                model_name=data.get("model"),
            )
            self.clients[provider] = client
            self.logger.info("GenAI Client created and stored.")
            return client

        else:
            self.logger.error(f"Unknown provider: {provider}")
            raise ValueError(f"Unknown provider: {provider}")
