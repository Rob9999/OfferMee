from typing import Any, Dict
import requests
from bs4 import BeautifulSoup

from offermee.AI.rfp_processor import RFPProcessor
from offermee.database.facades.main_facades import RFPFacade, ReadFacade
from offermee.database.models.main_models import RFPSource
from offermee.scraper.base_scraper import BaseScraper
from offermee.utils.config import Config
from offermee.utils.logger import CentralLogger


class BaseRFPScraper(BaseScraper):
    """
    General base class for scrapers.
    Provides basic functions such as HTTP fetching,
    HTML parsing, and unified logging.
    """

    def __init__(self, base_url):
        super().__init__(base_url)
        self.project_processor: RFPProcessor = RFPProcessor()

    def process(self, project: Dict[str, Any]) -> None:
        """
        Analyzes the rfp (request for proposal) description with an LLM and stores the extracted data.
        """
        self.logger.info(f"Processing project: {project.get('title', 'No title')}")
        analysis = self.project_processor.analyze_rfp(str(project))
        new_rfp = analysis.get("project") if analysis else {}
        if not new_rfp:
            self.logger.error(
                f"Analysis failed for project: {project.get('title', 'No title')}"
            )
            return
        try:
            original_link = new_rfp["original_link"] = new_rfp.get(
                "original_link", project["link"]
            )
            existing_project = ReadFacade.get_source_rule_unique_rfp_record(
                source=RFPSource.ONLINE, original_link=original_link
            )
            if existing_project:
                self.logger.info(f"RFP already exists: {new_rfp.get('title')}")
                return
            self.logger.info(f"AI RFP analysis: {new_rfp}")
            new_rfp["source"] = RFPSource.ONLINE
            RFPFacade.create(
                new_rfp, created_by=Config.get_instance().get_current_user()
            )
            self.logger.info(f"RFP saved: {new_rfp.get('title')}")
        except Exception as e:
            self.logger.exception(f"Error saving RFP: {e}")
