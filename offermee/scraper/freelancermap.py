from .base_scraper import BaseScraper


class FreelanceMapScraper(BaseScraper):
    SEARCH_URL = "https://www.freelancermap.de/projektboerse.html"

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
        Sucht Projekte auf Freelancermap basierend auf detaillierten Parametern.

        :param query: Suchbegriffe
        :param categories: Liste von Kategorien-IDs
        :param contract_types: Liste von Vertragsarten
        :param remote: Remote-Arbeitsanteil (Liste)
        :param industries: Liste von Industrie-IDs
        :param matching_skills: Liste von Skill-IDs
        :param countries: Liste von Länder-IDs
        :param states: Liste von Bundesland-IDs
        :param sort: Sortierparameter (Standard = 1)
        :param page: Seitennummer
        :param max_results: Max. Anzahl der Projekte
        :return: Liste der Projekte
        """
        params = {
            "query": query,
            "categories[]": categories,
            "projectContractTypes[]": contract_types,
            "remoteInPercent[]": remote,
            "industry[]": industries,
            "matchingSkills[]": matching_skills,
            "countries[]": countries,
            "states[]": states,
            "sort": sort,
            "pagenr": page,
            "hideAppliedProjects": "true",
        }

        # Filter leere Parameter
        params = {key: value for key, value in params.items() if value}

        html_content = self.fetch_page(self.SEARCH_URL, params=params)
        if not html_content:
            print("No content received.")
            return []

        soup = self.parse_html(html_content)
        projects = []

        # Projekte extrahieren
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
                description_tag.text.strip() if description_tag else "No description"
            )

            projects.append({"title": title, "link": link, "description": description})

        return projects
