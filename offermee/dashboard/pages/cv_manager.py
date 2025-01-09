import streamlit as st

from offermee.config import Config
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.web_dashboard import stop_if_not_logged_in
from offermee.database.database_manager import DatabaseManager
from offermee.database.db_connection import get_freelancer_by_name
from offermee.database.models.freelancer_model import FreelancerModel
import PyPDF2


def render():
    st.header("Upload CV")
    stop_if_not_logged_in()

    config = Config.get_instance()
    cv_candiate = st.text_input(
        label="Candiate", value=config.get_name_from_local_settings()
    )

    uploaded_file = st.file_uploader("Upload your resume (PDF):", type=["pdf"])
    if uploaded_file is not None:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Get CVProcessor and analyze cv text
        cv_processor = CVProcessor()
        cv_data = cv_processor.analyze_cv(text)

        if not cv_data:
            st.error("Fehler beim Analysieren des Lebenslaufs.")
            return

        st.write("Extrahierte Daten:", cv_data)

        # Zugriff auf extrahierte Personendaten
        person_data = cv_data.get("person", {})
        st.write("Extrahierte Personendaten:", person_data)

        person_name = CVProcessor.get_person_name(person_data, max_firstnames=2)
        st.write(person_name)

        soft_skills = CVProcessor.get_all_soft_skills(cv_data)
        tech_skills = CVProcessor.get_all_tech_skills(cv_data)

        # Determine the desired hourly rate
        desired_rate = st.slider(
            "Desired hourly rate (€)",
            min_value=0.0,
            max_value=500.0,  # Example upper limit
            value=(50.0, 150.0),  # Default range (min, max)
            step=10.0,
        )

        # Split the tuple into separate variables if needed
        desired_rate_min, desired_rate_max = desired_rate

        st.write(
            f"Minimum hourly rate: {desired_rate_min} €, Maximum hourly rate: {desired_rate_max} €"
        )

        if st.button("Save"):
            db_manager = DatabaseManager()
            session = db_manager.get_default_session()

            try:
                freelancer = get_freelancer_by_name(name=cv_candiate)
                if not freelancer:
                    freelancer = FreelancerModel(
                        name=person_name,
                        soft_skills=", ".join(soft_skills),
                        tech_skills=", ".join(tech_skills),
                        desired_rate_min=desired_rate_min,
                        desired_rate_max=desired_rate_max,
                    )
                    session.add(freelancer)
                else:
                    freelancer.name = cv_candiate
                    soft_skills = ", ".join(soft_skills)
                    tech_skills = ", ".join(tech_skills)
                    freelancer.desired_rate_min = desired_rate_min
                    freelancer.desired_rate_max = desired_rate_max
                session.commit()
                st.success("CV successfully saved and skills extracted!")
            except Exception as e:
                session.rollback()
                st.error(f"Error saving CV: {e}")
            finally:
                session.close()

        st.success("CV erfolgreich analysiert und gespeichert!")
