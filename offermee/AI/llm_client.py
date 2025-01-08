import logging
from abc import ABC, abstractmethod

from offermee.logger import CentralLogger


class LLMClient(ABC):
    def __init__(self, api_key, model_name):
        self.logger = CentralLogger.getLogger(__name__)

        self.api_key = api_key
        self.model_name = model_name
        self.setup_client()

        self.pompt_project_analyze = (
            "Bitte analysiere die folgende Projektbeschreibung und extrahiere die folgenden Informationen in einem JSON-Format:\n"
            "1. Location (Remote/On-site/Hybrid).\n"
            "2. Must-Have Requirements.\n"
            "3. Nice-To-Have Requirements.\n"
            "4. Tasks/Responsibilities.\n"
            "5. Max Hourly Rate (falls vorhanden).\n"
            "6. Other conditions.\n"
            "7. Contact Person (falls vorhanden).\n"
            "8. Project Provider.\n"
            "9. Project Start Date. Format: dd.mm.yyyy (passe ungenaue Angaben zu sinnvollen an)\n"
            "10. Original Link.\n\n"
            f"Projektbeschreibung:\n%%PROJECT_DESCRIPTION%%\n\n"
            "Bitte liefere die Ergebnisse als ein gültiges JSON-Objekt."
        )

    def set_project_analyze_prompt(self, prompt: str):
        self.pompt_project_analyze = prompt

    def make_project_analyze_prompt(self, project_description: str) -> str:
        return self.pompt_project_analyze.replace(
            "%%PROJECT_DESCRIPTION%%", project_description
        )

    @abstractmethod
    def setup_client(self):
        """Initialisiert den spezifischen LLM-Client."""
        pass

    @abstractmethod
    def analyze_project(self, project_description):
        """Analysiert die Projektbeschreibung und extrahiert relevante Informationen."""
        pass
