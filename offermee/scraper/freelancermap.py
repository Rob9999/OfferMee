from typing import List, Tuple, Dict, Any, Optional
from offermee.AI.rfp_processor import RFPProcessor
from offermee.htmls.save_utils import generate_filename_from_url, save_html
from offermee.utils.logger import CentralLogger
from offermee.scraper.base_rfp_scraper import BaseRFPScraper
from bs4 import BeautifulSoup

from offermee.utils.international import _T


class FreelanceMapScraper(BaseRFPScraper):
    """
    Scrapes RFPs (Requests For Proposals -> Projects) from the FreelancerMap platform.

    Supports searching with various parameters such as query terms, categories, contract types,
    remote options, industries, matching skills and location-based filtering. Also maps human-readable
    values to the identifiers expected by FreelancerMap.

    Features:
    - Parameter mapping with error logging for invalid/missing values.
    - Pagination support.
    - Extraction of project details (title, description, link, etc.).
    - Analysis of project descriptions via an LLM (e.g. GPT-4).
    - Storage of structured project data in the database.
    """

    BASE_URL = "https://www.freelancermap.de"
    SEARCH_URL = "https://www.freelancermap.de/projektboerse.html"

    # Mappings for countries, contract types, and remote options
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

    def __init__(self) -> None:
        super().__init__(self.BASE_URL)

    def map_params(
        self,
        contract_types: Optional[List[str]],
        remote: Optional[List[str]],
        countries: Optional[List[str]],
    ) -> Tuple[List[Any], List[Any], List[Any]]:
        """
        Maps enum values to IDs or strings expected by FreelancerMap.

        Parameters:
            contract_types (List[str]): List of contract types.
            remote (List[str]): List of remote work options.
            countries (List[str]): List of country names.

        Returns:
            Tuple containing:
                - List of mapped contract types.
                - List of mapped remote options.
                - List of mapped country identifiers.
        """
        mapped_contract_types: List[Any] = []
        if contract_types:
            for ct in contract_types:
                if ct in self.CONTRACT_TYPE_MAPPING:
                    mapped_contract_types.append(self.CONTRACT_TYPE_MAPPING[ct])
                else:
                    self.logger.warning(f"Invalid contract type value: {ct}")

        mapped_remote: List[Any] = []
        if remote:
            for r in remote:
                if r in self.REMOTE_MAPPING:
                    mapped_remote.append(self.REMOTE_MAPPING[r])
                else:
                    self.logger.warning(f"Invalid remote value: {r}")

        mapped_countries: List[Any] = []
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

    def parse_search_page_html(
        self, html_content: str, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        self.logger.info(
            f"Start parsing search page HTML content (max_results={max_results})."
        )
        rfps: List[Dict[str, Any]] = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            rfp_items = soup.find_all(
                "div", class_="project-container project card box", limit=max_results
            )
            for item in rfp_items:
                title_tag = item.find("a", class_="project-title")
                title = title_tag.get_text(strip=True) if title_tag else "No title"
                link = (
                    f"https://www.freelancermap.de{title_tag['href']}"
                    if title_tag and title_tag.get("href")
                    else "No link"
                )
                description_tag = item.find("div", class_="description")
                short_description = (
                    description_tag.get_text(strip=True)
                    if description_tag
                    else "No description"
                )
                rfp = {
                    "title": title,
                    "link": link,
                    "short-description": short_description,
                }
                rfps.append(rfp)
                self.logger.info(f"Parsed RFP: {rfp}")
        except Exception as e:
            self.logger.exception(f"Error while parsing search HTML: {e}")
        return rfps

    def parse_rfp_page_html(
        self, html_content: str, rfp: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.logger.info(
            f"Start parsing RFP page HTML (RFP: {rfp.get('title', 'No title')}, HTML size: {len(html_content)})."
        )
        # Save HTML to disk
        save_html(html_content, filename=generate_filename_from_url(rfp["link"]))
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            title_header_tag = soup.find("h1", class_="m-t-1 h2")
            title_header = (
                title_header_tag.get_text(strip=True)
                if title_header_tag
                else "No title header"
            )

            description_div = soup.find(
                "div", class_="projectcontent", itemprop="description"
            )
            description = ""
            keywords: List[str] = []
            if description_div:
                # Iterate over all child divs to extract keywords and description content
                for desc_div in description_div.find_all("div"):
                    class_attributes = desc_div.get("class", [])
                    if "keywords-container" in class_attributes:
                        for kw_span in desc_div.find_all(
                            "span", class_="keyword no-truncate"
                        ):
                            keywords.append(kw_span.get_text(strip=True))
                    elif "content" in class_attributes:
                        # Remove the header if present and get the rest of the text
                        description = desc_div.get_text(strip=False).replace(
                            '<h2 class="h4">Beschreibung</h2>', ""
                        )

            # Extract details from <dl> sections
            details: Dict[str, str] = {}
            for dl in soup.find_all("dl", class_="m-t-1"):
                dts = dl.find_all("dt")
                dds = dl.find_all("dd")
                for dt, dd in zip(dts, dds):
                    label = dt.get_text(strip=True).replace(":", "")
                    value = dd.get_text(strip=True)
                    details[label] = value

            rfp.update(
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
            self.logger.info(f"Parsed project details: {rfp}")
        except Exception as e:
            self.logger.exception(f"Error while parsing project HTML: {e}")
        return rfp

    def fetch(
        self,
        query: Optional[str] = None,
        categories: Optional[List[Any]] = None,
        contract_types: Optional[List[str]] = None,
        remote: Optional[List[str]] = None,
        industries: Optional[List[Any]] = None,
        matching_skills: Optional[List[Any]] = None,
        countries: Optional[List[str]] = None,
        states: Optional[List[Any]] = None,
        sort: int = 1,
        page: int = 1,
        max_results: int = 10,
        progress: Any = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetches RFPs from FreelancerMap based on detailed parameters.
        """
        try:
            mapped_contract_types, mapped_remote, mapped_countries = self.map_params(
                contract_types, remote, countries
            )
            params: Dict[str, Any] = {
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
            # Filter out empty parameters (keep zeros and non-empty lists)
            params = {
                key: value
                for key, value in params.items()
                if value not in (None, [], {})
            }

            search_page_html_content = self.fetch_page(self.SEARCH_URL, params=params)
            if not search_page_html_content:
                self.logger.error("No content received from search page.")
                return []
            rfps = self.parse_search_page_html(
                search_page_html_content, max_results=max_results
            )
            count = len(rfps)
            current: int = 0
            for rfp in rfps:
                current += 1
                project_page_html_content = self.fetch_page(rfp["link"])
                if not project_page_html_content:
                    self.logger.error(
                        f"No project page available for {rfp.get('title')}. Skipping."
                    )
                    continue
                rfp = self.parse_rfp_page_html(project_page_html_content, rfp=rfp)
                if progress:
                    progress.progress(
                        current / count,
                        f"{_T('Processing RFPs')}: {current} / {count}",
                    )
                # llm analysis and store in db
                self.process(rfp)
                if progress:
                    progress.progress(
                        current / count, f"{_T('Processed RFPs')}: {current} / {count}"
                    )
            return rfps
        except AttributeError as e:
            self.logger.exception(f"AttributeError while parsing project: {e}")
            return []
        except Exception as e:
            self.logger.exception(f"General error while fetching projects: {e}")
            return []

    def fetch_paginated(
        self,
        query: Optional[str] = None,
        categories: Optional[List[Any]] = None,
        contract_types: Optional[List[str]] = None,
        remote: Optional[List[str]] = None,
        industries: Optional[List[Any]] = None,
        matching_skills: Optional[List[Any]] = None,
        countries: Optional[List[str]] = None,
        states: Optional[List[Any]] = None,
        sort: int = 1,
        max_pages: int = 5,
        max_results: int = 50,
        progress: Any = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetches multiple pages of RFPs and aggregates them.
        """
        all_rfps: List[Dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            rfps = self.fetch(
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
                max_results=max_results,  # max results per page can be controlled if needed
                progress=progress,
            )
            if not rfps:
                break  # No more RFPs found
            for rfp in rfps:
                all_rfps.append(rfp)
                if len(all_rfps) >= max_results:
                    break
            if len(all_rfps) >= max_results:
                break
            # Optionally update progress across pages.
            if progress:
                overall_progress = page / max_pages
                progress.progress(
                    overall_progress, f"{_T('Processed page')}: {page} / {max_pages}"
                )
        return all_rfps
