from abc import ABC, abstractmethod


class Scraper(ABC):
    """
    Abstract interface for all scrapers.
    Defines the methods that a concrete scraper should have.
    """

    @abstractmethod
    def fetch_page(self, url, params=None):
        """
        Sends an HTTP request and returns the content of the page.
        """
        pass

    @abstractmethod
    def fetch(self, *args, **kwargs):
        """
        Fetches (single page).
        """
        pass

    @abstractmethod
    def fetch_paginated(self, *args, **kwargs):
        """
        Fetches (multiple pages, paginated).
        """
        pass

    @abstractmethod
    def parse_html(self, *args, **kwargs):
        """
        Parses HTML content and returns a BeautifulSoup object.
        """
        pass

    @abstractmethod
    def process(self, *args, **kwargs) -> None:
        """
        Analyzes and processes the scraped content (may use an LLM for analysis and may stores the extracted data to db).
        """
        pass
