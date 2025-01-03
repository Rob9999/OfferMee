import logging
from offermee.AI.llm_client import LLMClient
from offermee.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GENAI_API_KEY,
    GENAI_MODEL,
    # Weitere API-Keys und Modelle hier hinzufügen
)

# Import der LLMClient-Klassen
from offermee.AI.openai_client import OpenAIClient
from offermee.AI.genai_client import GenAIClient


class AIManager:
    _instance = None

    def __new__(cls, default_client: str = None):
        if cls._instance is None:
            cls._instance = super(AIManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, default_client: str = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        # Logger initialisieren
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        # Initialisieren eines Dictionaries zur Speicherung der Clients
        self.clients = {}
        self.set_default_client(default_client)
        self._initialized = True

    def set_default_client(self, provider: str):
        """
        Setzt den Standard-LLM-Client für die Analyse von Projektbeschreibungen.

        :param provider: Name des Anbieters (z.B. 'openai', 'genai')
        """
        if not provider:
            self.logger.warning("Es wurde kein Standard-LLM-Client festgelegt.")
            self.default_client = None
            return

        if provider is None:
            self.logger.warning("Es wurde kein Standard-LLM-Client festgelegt.")
            self.default_client = None
            return

        provider = provider.lower()

        if provider in ["openai", "genai"]:
            self.logger.debug(
                f"Der {provider}-Client wurde als Standard-LLM-Client festgelegt."
            )
            self.default_client = provider
        else:
            self.logger.error(f"Unbekannter Anbieter: {provider}")
            raise ValueError(f"Unbekannter Anbieter: {provider}")

    def get_default_client(self) -> "LLMClient":
        """
        Gibt den Standard-LLM-Client zurück.
        """
        if self.default_client:
            self.logger.debug(
                f"Rückgabe des Standard-LLM-Clients: {self.default_client}"
            )
            return self.get_client(self.default_client)
        else:
            self.logger.error("Es wurde kein Standard-LLM-Client festgelegt.")
            raise ValueError("Es wurde kein Standard-LLM-Client festgelegt.")

    def get_client(self, provider: str) -> "LLMClient":
        """
        Gibt eine Instanz des gewünschten LLM-Clients zurück.

        :param provider: Name des Anbieters (z.B. 'openai', 'genai')
        :return: Instanz eines LLMClient
        """
        provider = provider.lower()

        if provider in self.clients:
            self.logger.debug(
                f"Rückgabe des bereits initialisierten {provider}-Clients."
            )
            return self.clients[provider]

        if provider == "openai":
            client = OpenAIClient(api_key=OPENAI_API_KEY, model_name=OPENAI_MODEL)
            self.clients[provider] = client
            self.logger.info("OpenAI Client erstellt und gespeichert.")
            return client

        elif provider == "genai":
            client = GenAIClient(api_key=GENAI_API_KEY, model_name=GENAI_MODEL)
            self.clients[provider] = client
            self.logger.info("GenAI Client erstellt und gespeichert.")
            return client

        else:
            self.logger.error(f"Unbekannter Anbieter: {provider}")
            raise ValueError(f"Unbekannter Anbieter: {provider}")
