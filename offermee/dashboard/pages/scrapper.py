import streamlit as st
from offermee.scraper.freelancermap import FreelanceMapScraper
from offermee.database.models.intermediate_project_model import IntermediateProjectModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Datenbankverbindung einrichten
engine = create_engine("sqlite:///offermee.db")
Session = sessionmaker(bind=engine)
session = Session()


def render():
    st.header("Projektsucheinstellungen")

    # Plattformauswahl
    platforms = ["FreelancerMap"]  # Weitere Plattformen später hinzufügen
    platform = st.selectbox("Plattform auswählen:", platforms)

    # Suchparameter
    query = st.text_input("Suchbegriffe (z. B. Python Developer)")
    location = st.text_input("Ort (optional)")
    max_pages = st.number_input("Max. Seitenanzahl", min_value=1, value=3)
    max_results = st.number_input("Max. Projekte", min_value=1, value=10)

    # Scraper ausführen
    if st.button("Scraping starten"):
        if platform == "FreelancerMap":
            scraper = FreelanceMapScraper("https://www.freelancermap.de")
            projects = scraper.fetch_projects_paginated(
                query=query,
                countries=[1],  # Beispiel: Deutschland
                max_pages=max_pages,
                max_results=max_results,
            )

            # Ergebnisse anzeigen und speichern
            if projects:
                st.success(f"{len(projects)} Projekte gefunden!")
                for project in projects:
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
                session.commit()
            else:
                st.warning("Keine Projekte gefunden.")
