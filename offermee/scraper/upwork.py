from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from offermee.scraper.base_rfp_scraper import BaseRFPScraper
from offermee.utils.international import _T


class UpworkScraper(BaseRFPScraper):
    """
    Scraper for Upwork projects.
    This class scrapes job listings directly from Upwork's search page.
    """

    BASE_URL = "https://www.upwork.com"
    SEARCH_URL = "https://www.upwork.com/freelance-jobs/"

    def __init__(self) -> None:
        super().__init__(self.BASE_URL)

    def fetch(
        self, query: str, max_results: int = 10, progress: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches projects from Upwork based on the search query.

        Args:
            query (str): Search term.
            max_results (int): Maximum number of results.
            progress (Optional[Any]): An optional progress object to update the progress.

        Returns:
            List[Dict[str, Any]]: List of found projects.
        """
        try:
            params = {"q": query}
            self.logger.info(f"Fetching Upwork projects with query: '{query}'")
            html_content = self.fetch_page(self.SEARCH_URL, params=params)
            if not html_content:
                self.logger.warning("No content received from Upwork.")
                return []

            # Parse jobs from the HTML
            projects = self.parse_search_page_html(html_content, max_results)

            # If we want to process each project (e.g. LLM analysis, DB storage), do it here.
            total_projects = len(projects)
            for idx, project in enumerate(projects, start=1):
                if progress:
                    progress.progress(
                        idx / total_projects,
                        f"{_T('Processing RFPs')}: {idx} / {total_projects}",
                    )
                # LLM analysis and store in DB
                self.process(project)
                if progress:
                    progress.progress(
                        idx / total_projects,
                        f"{_T('Processed RFPs')}: {idx} / {total_projects}",
                    )

            return projects
        except Exception as e:
            self.logger.error(f"General error while fetching projects: {e}")
            return []

    def parse_search_page_html(
        self, html_content: str, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Parses the Upwork job search page HTML and extracts job listings.

        Args:
            html_content (str): The HTML content of the Upwork search page.
            max_results (Optional[int]): Maximum number of job listings to extract.

        Returns:
            List[Dict[str, Any]]: List of extracted job listings.
        """
        self.logger.info("Parsing Upwork job search page.")
        projects: List[Dict[str, Any]] = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Each job listing is often in a section or article tag.
            # This may need updating if Upwork changes its HTML structure.
            job_items = soup.find_all("section", class_="up-card-section")

            for job in job_items[:max_results]:
                title_tag = job.find("h2", class_="job-title")
                title = title_tag.get_text(strip=True) if title_tag else "No title"

                link_tag = job.find("a", class_="job-title-link")
                if link_tag and link_tag.get("href"):
                    link = self.BASE_URL + link_tag["href"]
                else:
                    link = "No link"

                desc_tag = job.find("div", class_="job-description")
                description = (
                    desc_tag.get_text(strip=True) if desc_tag else "No description"
                )

                project = {
                    "title": title,
                    "link": link,
                    "description": description,
                }
                projects.append(project)
                self.logger.info(f"Parsed job: {title}")
        except Exception as e:
            self.logger.error(f"Error while parsing Upwork job search page: {e}")
        return projects

    def fetch_paginated(
        self,
        query: str,
        max_pages: int = 5,
        max_results: int = 50,
        progress: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetches multiple pages of projects and aggregates them.

        Args:
            query (str): Search term.
            max_pages (int): Maximum number of pages to fetch.
            max_results (int): Maximum number of projects (total).
            progress (Optional[Any]): An optional progress object to update the progress.

        Returns:
            List[Dict[str, Any]]: Aggregated list of projects.
        """
        all_projects: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            self.logger.info(f"Fetching page {page} with query: '{query}'")
            # We'll just reuse fetch but it doesn't take page param currently.
            # If needed, we can adapt param usage or pass page via query.
            projects = self.fetch(query, max_results=max_results, progress=progress)
            if not projects:
                break  # No more projects found
            all_projects.extend(projects)
            if len(all_projects) >= max_results:
                all_projects = all_projects[:max_results]
                break
            if progress:
                overall_progress = page / max_pages
                progress.progress(
                    overall_progress,
                    f"{_T('Processed page')}: {page} / {max_pages}",
                )
        return all_projects
