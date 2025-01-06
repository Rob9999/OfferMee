import streamlit as st
from offermee.database.db_connection import connect_to_db
from offermee.enums.contract_types import ContractType
from offermee.enums.countries import Country
from offermee.enums.sites import Site
from offermee.scraper.freelancermap import FreelanceMapScraper
from offermee.database.models.intermediate_project_model import IntermediateProjectModel


def render():
    st.header("Projektsucheinstellungen")

    # Plattformauswahl
    platforms = ["FreelancerMap"]  # Weitere Plattformen später hinzufügen
    platform = st.selectbox("Plattform auswählen:", platforms)

    # Suchparameter
    # Query
    query = st.text_input("Suchbegriffe (z. B. Python Developer)")
    # Location (City)
    location = st.text_input("Ort (optional)")
    # Countries [Deutschland, Österreich, Schweiz, Europa, Erde :)]
    country_selection = st.selectbox("Länder auswählen:", Country.values())
    # Contract Types [Contractor, ANÜ, Festanstellung]
    contract_type_selection = st.selectbox(
        "Contract Typ auswählen:", ContractType.values()
    )
    # Site ["remote", "onsite", "hybrid"]
    site_selection = st.selectbox("Site auswählen:", Site.values())

    max_pages = st.number_input("Max. Seitenanzahl", min_value=1, value=3)
    max_results = st.number_input("Max. Projekte", min_value=1, value=10)
    min_hourly_rate = st.number_input("Min. Stundensatz (€)", min_value=0, value=50)
    max_hourly_rate = st.number_input("Max. Stundensatz (€)", min_value=0, value=100)

    # Scraper ausführen
    if st.button("Scraping starten"):
        if platform == "FreelancerMap":
            scraper = FreelanceMapScraper("https://www.freelancermap.de")
            projects = scraper.fetch_projects_paginated(
                query=query,
                categories=None,
                contract_types=ContractType(contract_type_selection).name,
                remote=Site(site_selection).name,
                industries=None,
                matching_skills=None,
                countries=Country(country_selection).name,
                states=None,
                sort=1,
                max_pages=max_pages,
                max_results=max_results,
            )

            # Ergebnisse anzeigen und speichern
            if projects:
                # Session starten
                session = connect_to_db()

                try:
                    st.success(f"{len(projects)} Projekte gefunden!")
                    for project in projects:
                        try:
                            st.subheader(project["title"])
                            st.write(f"Beschreibung: {project['description']}")
                            st.write(f"[Link zum Projekt]({project['link']})")

                            # Temporäre Speicherung in der Datenbank
                            temp_project = IntermediateProjectModel(
                                title=project["title"],
                                description=project["description"],
                                analysis=None,  # Analyse wird später hinzugefügt
                                is_saved=False,
                            )
                            session.add(temp_project)
                        except Exception as e:
                            session.rollback()
                            print(f"Fehler beim Speichern von {project['title']}: {e}")
                    session.commit()
                finally:
                    session.close()
            else:
                st.warning("Keine Projekte gefunden.")
