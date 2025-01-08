import streamlit as st
from offermee.dashboard.web_dashboard import stop_if_not_logged_in
from offermee.database.database_manager import DatabaseManager
from offermee.database.models.freelancer_model import FreelancerModel
import PyPDF2
import re


def extract_skills(text):
    """
    Extrahiert Fähigkeiten aus dem CV-Text.
    Dies ist eine einfache Implementierung und sollte für Produktionszwecke verfeinert werden.
    """
    # Beispiel: Extraktion von Schlagwörtern nach "Skills" Abschnitt
    skills = []
    skills_section = re.search(r"Skills?:\s*(.*)", text, re.IGNORECASE)
    if skills_section:
        skills_text = skills_section.group(1)
        skills = [skill.strip() for skill in skills_text.split(",")]
    return skills


def extract_name(text):
    """
    Extrahiert den Namen des Freelancers aus dem CV-Text.
    """
    # Beispiel: Annahme, dass der Name in der ersten Zeile steht
    lines = text.strip().split("\n")
    return lines[0].strip() if lines else "Unbekannt"


def render():
    st.header("CV hinterlegen")
    stop_if_not_logged_in()

    uploaded_file = st.file_uploader(
        "Laden Sie Ihren Lebenslauf (PDF) hoch:", type=["pdf"]
    )
    if uploaded_file is not None:
        # Extraktion von Text aus dem PDF
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Extrahieren von relevanten Informationen
        name = extract_name(text)
        skills = extract_skills(text)

        # Optional: Extrahieren des gewünschten Stundensatzes
        # Hier könnte eine weitere Funktion implementiert werden, um den Stundensatz zu extrahieren

        # Beispiel: Eingabe des gewünschten Stundensatzes durch den Benutzer
        desired_rate = st.number_input(
            "Gewünschter Stundensatz (€)", min_value=0.0, step=10.0
        )

        if st.button("Speichern"):
            db_manager = DatabaseManager()
            session = db_manager.get_default_session()

            try:
                freelancer = session.query(FreelancerModel).first()
                if not freelancer:
                    freelancer = FreelancerModel(
                        name=name,
                        skills=", ".join(skills),
                        desired_rate=desired_rate,
                    )
                    session.add(freelancer)
                else:
                    freelancer.name = name
                    freelancer.skills = ", ".join(skills)
                    freelancer.desired_rate = desired_rate
                session.commit()
                st.success("CV erfolgreich gespeichert und Skills extrahiert!")
            except Exception as e:
                session.rollback()
                st.error(f"Fehler beim Speichern des CV: {e}")
            finally:
                session.close()
