from abc import ABC, abstractmethod


class Scraper(ABC):
    """
    Abstract interface for all scrapers.
    Defines the methods that a concrete scraper should have.
    """

    @abstractmethod
    def fetch_rfps(self, *args, **kwargs):
        """
        Fetches projects (single page).
        """
        pass

    @abstractmethod
    def fetch_rfps_paginated(self, *args, **kwargs):
        """
        Fetches projects (multiple pages, paginated).
        """
        pass
