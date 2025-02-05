from abc import ABC, abstractmethod
from offermee.utils.logger import CentralLogger


class LLMClient(ABC):
    def __init__(self, api_key, model_name):
        self.logger = CentralLogger.getLogger(__name__)

        self.api_key = api_key
        self.model_name = model_name
        self.setup_client()

    @abstractmethod
    def setup_client(self):
        """Initialisiert den spezifischen LLM-Client."""
        pass

    @abstractmethod
    def extract_to_json(self, project_description):
        """Extrahiert relevante Informationen to JSON."""
        pass
