import requests
from bs4 import BeautifulSoup

from offermee.utils.logger import CentralLogger
from offermee.scraper.scraper_interface import Scraper


class BaseScraper(Scraper):
    """
    General base class for scrapers.
    Provides basic functions such as HTTP fetching,
    HTML parsing, and unified logging.
    """

    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
        }
        # Set up logger
        self.logger = CentralLogger.getLogger(__name__)

    def fetch_page(self, url, params=None):
        """
        Sends an HTTP request and returns the content of the page.
        """
        try:
            self.logger.info(f"fetch_page: url='{url}', params='{params}'")
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching page: {e}")
            return None

    def parse_html(self, html_content):
        """
        Parses HTML content and returns a BeautifulSoup object.
        """
        return BeautifulSoup(html_content, "html.parser")

    def fetch_rfps(self, *args, **kwargs):
        """
        Default implementation, can be overridden by subclasses.
        """
        raise NotImplementedError("fetch_rfps must be overridden in the subclass.")

    def fetch_rfps_paginated(self, *args, **kwargs):
        """
        Default implementation, can be overridden by subclasses.
        """
        raise NotImplementedError(
            "fetch_rfps_paginated must be overridden in the subclass."
        )
