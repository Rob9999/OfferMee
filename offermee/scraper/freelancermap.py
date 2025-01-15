import os
from urllib.parse import urlparse
from sqlalchemy.orm import sessionmaker

from offermee.AI.project_processor import ProjectProcessor
from offermee.database.facades.main_facades import ProjectFacade
from offermee.database.transformers.project_model_transformer import json_to_db
from offermee.htmls.save_utils import generate_filename_from_url, save_html
from offermee.logger import CentralLogger
from offermee.scraper.base_scraper import BaseScraper
from offermee.database.database_manager import DatabaseManager
import requests
from bs4 import BeautifulSoup, Tag
import json


class FreelanceMapScraper(BaseScraper):
    """
    This class is designed to scrape projects from the FreelancerMap platform.

    It supports searching with multiple parameters, such as query terms, categories, contract types,
    remote options, industries, matching skills, and location-based filtering. The class handles
    mapping human-readable values (like country names) to the identifiers expected by FreelancerMap.

    The scraper includes functionality for:
    - Logging and error handling for invalid or missing parameters.
    - Paginated fetching of projects.
    - Extraction of project details (title, description, and link).
    - Analysis of project descriptions using LLM (GPT-4).
    - Storing structured project data in the database.
    """

    BASE_URL = "https://www.freelancermap.de"
    SEARCH_URL = "https://www.freelancermap.de/projektboerse.html"

    # Mapping for countries, contract types, and remote options
    COUNTRY_MAPPING = {
        "Deutschland": 1,
        "Österreich": 2,
        "Schweiz": 3,
        "DACH": [1, 2, 3],
        "EU": "EU",
        "Europa": "Europe",
        "Erde": "World",
    }

    CONTRACT_TYPE_MAPPING = {
        "Contractor": "contracting",
        "ANÜ": "employee_leasing",
        "Festanstellung": "permanent_position",
    }

    REMOTE_MAPPING = {
        "remote": 100,
        "onsite": 0,
        "hybrid": 50,
    }

    def __init__(self):
        # Call the constructor of the base class
        super().__init__(self.BASE_URL)
        self.logger = CentralLogger.getLogger(__name__)
        self.project_processor = ProjectProcessor()

    def map_params(self, contract_types, remote, countries):
        """
        Maps Enum values to the IDs or strings expected by FreelancerMap.

        Parameters:
        - contract_types (list): List of contract types to be mapped.
        - remote (list): List of remote work options to be mapped.
        - countries (list): List of country names to be mapped.

        Returns:
        - tuple: Mapped contract types, remote options, and country identifiers.

        This function ensures:
        - Invalid or missing values are skipped.
        - Warnings for invalid values are logged for later review.

        Example:
        If an invalid contract type is provided, such as "InvalidType", it will be ignored and logged as a warning.
        Valid entries like "Contractor" will be mapped correctly to "contracting".
        """
        mapped_contract_types = []
        if contract_types:
            for ct in contract_types:
                if ct in self.CONTRACT_TYPE_MAPPING:
                    mapped_contract_types.append(self.CONTRACT_TYPE_MAPPING[ct])
                else:
                    self.logger.warning(f"Invalid contract type value: {ct}")

        mapped_remote = []
        if remote:
            for r in remote:
                if r in self.REMOTE_MAPPING:
                    mapped_remote.append(self.REMOTE_MAPPING[r])
                else:
                    self.logger.warning(f"Invalid remote value: {r}")

        mapped_countries = []
        if countries:
            for country in countries:
                mapped_value = self.COUNTRY_MAPPING.get(country)
                if isinstance(mapped_value, list):
                    mapped_countries.extend(mapped_value)
                elif mapped_value:
                    mapped_countries.append(mapped_value)
                else:
                    self.logger.warning(f"Invalid country value: {country}")

        return mapped_contract_types, mapped_remote, mapped_countries

    def parse_search_page_html(self, html_content, max_results=None):
        self.logger.info(
            f"Start parsing search page html content (max_results={max_results})."
        )
        projects = []
        try:
            # HTML parsen
            search_page_soup = BeautifulSoup(html_content, "html.parser")
            # Projekte aus der Liste extrahieren
            for item in search_page_soup.find_all(
                "div", class_="project-container project card box", limit=max_results
            ):
                title_tag = item.find("a", class_="project-title")
                title = title_tag.text.strip() if title_tag else "No title"
                link = (
                    f"https://www.freelancermap.de{title_tag['href']}"
                    if title_tag
                    else "No link"
                )
                description_tag = item.find("div", class_="description")
                short_description = (
                    description_tag.text.strip()
                    if description_tag
                    else "No description"
                )
                project = {
                    "title": title,
                    "link": link,
                    "short-description": short_description,
                }
                projects.append(project)
                self.logger.info(
                    f"Parsed from html content the project: {str(project)}"
                )
        except Exception as e:
            self.logger.error(f"Error while parsing html: {e}")
        finally:
            return projects

    def parse_project_page_html(self, html_content, project):
        self.logger.info(
            f"Start parsing project page html content (count: {str(project)}, html size: {len(html_content)})."
        )

        # save html to disk
        save_html(html_content, filename=generate_filename_from_url(project["link"]))

        try:
            # HTML parsen
            project_page_soup = BeautifulSoup(html_content, "html.parser")

            # Titel extrahieren
            title_header_tag = project_page_soup.find("h1", class_="m-t-1 h2")
            title_header = (
                title_header_tag.get_text(strip=True)
                if title_header_tag
                else "No title header"
            )

            # Get project content description
            description_div = project_page_soup.find(
                "div", class_="projectcontent", itemprop="description"
            )

            # Beschreibung extrahieren
            # Hier suchen wir nach dem h2 mit Text "Beschreibung"
            # und holen uns den nächsten div.content
            description = ""
            keywords = []
            if description_div:
                description_divs: list[Tag] = description_div.find_all("div")
                for desc_div in description_divs:
                    class_attributes = desc_div.get_attribute_list("class")
                    for class_attribute in class_attributes:
                        if (
                            class_attribute
                            == "keywords-container"  # keywords-container content
                        ):
                            # Extract keywords
                            # print(f"FOUND keywords-container content:\n{desc_div}")
                            keyword_spans = desc_div.find_all(
                                "span", class_="keyword no-truncate"
                            )
                            for kw_span in keyword_spans:
                                keywords.append(kw_span.get_text(strip=True))
                        elif class_attribute == "content":
                            # Extract description
                            # print(f"FOUND content:\n{desc_div}")
                            description = desc_div.get_text(strip=False).replace(
                                '<h2 class="h4">Beschreibung</h2>',
                                "",  # remove header and take raw text
                            )
            # Details aus dem <dl>-Bereich extrahieren (unverändert)
            details = {}
            details_section = project_page_soup.find_all("dl", class_="m-t-1")
            for dl in details_section:
                for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
                    label = dt.get_text(strip=True).replace(":", "")
                    value = dd.get_text(strip=True)
                    details[label] = value

            # Projekt-Daten sammeln
            project.update(
                {
                    "title-header": title_header,
                    "description": description,
                    "keywords": keywords,
                    "project-details": {
                        "start": details.get("Start", "No start date"),
                        "workload": details.get("Auslastung", "No workload"),
                        "duration": details.get("Dauer", "No duration"),
                        "provider": details.get("Von", "No provider"),
                        "date-posted": details.get("Eingestellt", "No date posted"),
                        "contact-person": details.get(
                            "Ansprechpartner", "No contact person"
                        ),
                        "provider-project-id": details.get(
                            "Projekt-ID", "No project ID"
                        ),
                        "industry": details.get("Branche", "No industry"),
                        "contract-type": details.get("Vertragsart", "No contract type"),
                        "type-of-assignment": details.get(
                            "Einsatzart", "No type of assignment"
                        ),
                    },
                }
            )

            self.logger.info(f"Parsed from html content the project: {str(project)}")
        except Exception as e:
            self.logger.error(f"Error while parsing html: {e}")
        finally:
            return project

    def fetch_projects(
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
        page=1,
        max_results=10,
    ) -> list:
        """
        Fetches projects from FreelancerMap based on detailed parameters.

        Parameters:
        - query (str): Search terms.
        - categories (list): List of category IDs.
        - contract_types (list): List of contract type identifiers.
        - remote (list): List of remote work options.
        - industries (list): List of industry IDs.
        - matching_skills (list): List of skill IDs.
        - countries (list): List of country identifiers.
        - states (list): List of state identifiers.
        - sort (int): Sorting option.
        - page (int): Page number for pagination.
        - max_results (int): Maximum number of projects to fetch.

        Returns:
        - list: List of project dictionaries with title, link, and description.
        """
        try:
            # Map the Enum values
            mapped_contract_types, mapped_remote, mapped_countries = self.map_params(
                contract_types, remote, countries
            )

            params = {
                "query": query,
                "categories[]": categories,
                "projectContractTypes[]": mapped_contract_types,
                "remoteInPercent[]": mapped_remote,
                "industry[]": industries,
                "matchingSkills[]": matching_skills,
                "countries[]": mapped_countries,
                "states[]": states,
                "sort": sort,
                "pagenr": page,
                "hideAppliedProjects": "true",
            }

            # Filter empty parameters
            params = {key: value for key, value in params.items() if value}

            search_page_html_content = self.fetch_page(self.SEARCH_URL, params=params)
            if not search_page_html_content:
                self.logger.error("No content received from the page.")
                return []
            # parse for projects
            projects = self.parse_search_page_html(
                search_page_html_content, max_results=max_results
            )
            for project in projects:
                # fetch project page
                project_page_html_content = self.fetch_page(project["link"])
                if not project_page_html_content:
                    self.logger.error(
                        f"No project page for '{str(project)}' available. SKIP"
                    )
                    continue
                # parse each project html page
                project = self.parse_project_page_html(
                    project_page_html_content, project=project
                )
                self.process_project(project)  # Analyze and store to db
            return projects
        except AttributeError as e:
            self.logger.error(f"AttributeError beim Parsen eines Projekts: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Allgemeiner Fehler beim Abrufen von Projekten: {e}")
            return []

    def process_project(self, project):
        """
        Analyzes the project description with the LLM and stores the extracted data.

        Args:
            project (dict): Dictionary with project information (title, link, description).
        """
        self.logger.info(f"Processing project:\n{str(project)}")
        analysis = self.project_processor.analyze_project(str(project))
        if not (analysis and analysis.get("project")):
            self.logger.error(f"Analysis failed for project: {project['title']}")
            return

        try:
            existing_project = ProjectFacade.get_first_by(original_link=project["link"])
            if existing_project:
                self.logger.info(f"Project already exists: {project['title']}")
                return
            # enrich analysis
            self.logger.info(f"AI project analysis:\n{analysis}")
            new_project = json_to_db(analysis)
            ProjectFacade.create(new_project)
            self.logger.info(f"Project saved: {new_project.title}")
        except Exception as e:
            self.logger.error(f"Error saving project: {e}")

    def fetch_projects_paginated(
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

        Parameters:
        - query (str): Search terms.
        - categories (list): List of category IDs.
        - contract_types (list): List of contract type identifiers.
        - remote (list): List of remote work options.
        - industries (list): List of industry IDs.
        - matching_skills (list): List of skill IDs.
        - countries (list): List of country identifiers.
        - states (list): List of state identifiers.
        - sort (int): Sorting option.
        - max_pages (int): Maximum number of pages to fetch.
        - max_results (int): Maximum number of projects to return.

        Returns:
        - list: List of aggregated project dictionaries.
        """
        all_projects = []
        for page in range(1, max_pages + 1):
            projects: list = self.fetch_projects(
                query=query,
                categories=categories,
                contract_types=contract_types,
                remote=remote,
                industries=industries,
                matching_skills=matching_skills,
                countries=countries,
                states=states,
                sort=sort,
                page=page,
                max_results=max_results,
            )

            if not projects:
                break  # No more projects found

            for project in projects:
                all_projects.append(project)
                # self.logger.info(f"Found Project: {project}")
                if len(all_projects) >= max_results:
                    break  # Maximum number reached

            if len(all_projects) >= max_results:
                break

        return all_projects
