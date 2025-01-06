import logging
import json
from sqlalchemy.orm import sessionmaker

from offermee.scraper.base_scraper import BaseScraper
from offermee.database.database_manager import DatabaseManager
from offermee.database.models.base_project_model import BaseProjectModel
from offermee.database.models.enums.project_status import ProjectStatus
from offermee.AI.ai_manager import AIManager


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
        # Initialize LLM client
        self.llm_client = AIManager().get_default_client()
        # Initialize database manager
        self.db_manager = DatabaseManager()
        self.Session = sessionmaker(bind=self.db_manager.engine)

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
    ):
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

            html_content = self.fetch_page(self.SEARCH_URL, params=params)
            if not html_content:
                self.logger.error("No content received from the page.")
                return []

            soup = self.parse_html(html_content)
            projects = []

            for item in soup.find_all(
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
                description = (
                    description_tag.text.strip()
                    if description_tag
                    else "No description"
                )

                projects.append(
                    {"title": title, "link": link, "description": description}
                )

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
        analysis_json = self.llm_client.analyze_project(project["description"])
        if not analysis_json:
            self.logger.error(f"Analysis failed for project: {project['title']}")
            return

        try:
            analysis = json.loads(analysis_json)
            project["analysis"] = analysis
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for project {project['title']}: {e}")
            return

        session = self.Session()
        try:
            existing_project = (
                session.query(BaseProjectModel)
                .filter_by(original_link=project["link"])
                .first()
            )
            if existing_project:
                self.logger.info(f"Project already exists: {project['title']}")
                return

            new_project = BaseProjectModel(
                title=project["title"],
                description=project["description"],
                location=analysis.get("Location"),
                must_haves=DatabaseManager.join_list(
                    analysis.get("Must-Have Requirements", [])
                ),
                nice_to_haves=DatabaseManager.join_list(
                    analysis.get("Nice-To-Have Requirements", [])
                ),
                tasks=DatabaseManager.join_list(
                    analysis.get("Tasks/Responsibilities", [])
                ),
                hourly_rate=analysis.get("Max Hourly Rate", 0.0),
                other_conditions=DatabaseManager.join_list(
                    analysis.get("Other conditions", [])
                ),
                contact_person=analysis.get("Contact Person", ""),
                provider=analysis.get("Project Provider", ""),
                start_date=DatabaseManager.parse_date(
                    analysis.get("Project Start Date")
                ),
                original_link=project["link"],
                status=ProjectStatus.NEW,
            )
            session.add(new_project)
            session.commit()
            self.logger.info(f"Project saved: {new_project.title}")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error saving project: {e}")
        finally:
            session.close()

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
            projects = self.fetch_projects(
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
                self.process_project(project)  # Analyze and save
                all_projects.append(project)
                if len(all_projects) >= max_results:
                    break  # Maximum number reached

            if len(all_projects) >= max_results:
                break

        return all_projects
