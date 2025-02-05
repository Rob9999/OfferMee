import logging
from bs4 import BeautifulSoup

from offermee.scraper.base_scraper import BaseScraper


class UpworkScraper(BaseScraper):
    """
    Scraper for Upwork projects.
    This class uses the RSS feed from Upwork to collect projects based on search parameters.
    """

    BASE_URL = "https://www.upwork.com"
    SEARCH_URL = "https://www.upwork.com/ab/feed/jobs/rss"

    def __init__(self):
        super().__init__(self.BASE_URL)
        # Upwork-specific configurations could be added here.

    def fetch_rfps(self, query, max_results=10):
        """
        Fetches projects from Upwork based on the search query.
        """
        try:
            params = {
                "q": query,
                "sort": "recency",
                "paging": f"1;{max_results}",  # Example for pagination
            }
            self.logger.info(f"Fetching Upwork projects with query: '{query}'")
            xml_content = self.fetch_page(self.SEARCH_URL, params=params)
            if not xml_content:
                self.logger.warning("No content received from Upwork.")
                return []

            soup = BeautifulSoup(xml_content, "xml")
            projects = []
            for item in soup.find_all("item", limit=max_results):
                title = item.title.text if item.title else "No title"
                link = item.link.text if item.link else "No link"
                description = (
                    item.description.text if item.description else "No description"
                )

                projects.append(
                    {"title": title, "link": link, "description": description}
                )

            self.logger.info(f"Found {len(projects)} projects from Upwork.")
            return projects
        except AttributeError as e:
            self.logger.error(f"AttributeError beim Parsen eines Projekts: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Allgemeiner Fehler beim Abrufen von Projekten: {e}")
            return []

    def fetch_rfps_paginated(
        self,
        query=None,
        categories=None,
        contract_types=None,
        remote=None,
        industries=None,
        matching_skills=None,
        countries=None,
        states=None,
        sort=1,
        max_pages=5,
        max_results=50,
    ):
        """
        Fetches multiple pages of projects and aggregates them.
        """
        all_projects = []
        for page in range(1, max_pages + 1):
            current_query = f"{query} page:{page}"
            projects = self.fetch_rfps(query=current_query, max_results=max_results)

            if not projects:
                break  # No more projects found

            all_projects.extend(projects)

            # If we want to limit the total number:
            if len(all_projects) >= max_results:
                all_projects = all_projects[:max_results]
                break

        return all_projects
