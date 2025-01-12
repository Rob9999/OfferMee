import json
import streamlit as st

from offermee.config import Config
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.web_dashboard import log_error, log_info, stop_if_not_logged_in
from offermee.database.db_connection import (
    get_cv_by_freelancer_id,
    get_freelancer_by_name,
    session_scope,
)
from offermee.database.models.cv_model import CVModel
from offermee.database.models.freelancer_model import FreelancerModel
import PyPDF2


def render():
    st.header("Upload CV")
    stop_if_not_logged_in()

    config = Config.get_instance()
    cv_candiate = st.text_input(
        label="Candidate", value=config.get_name_from_local_settings()
    )

    uploaded_file = st.file_uploader("Upload your resume (PDF):", type=["pdf"])
    if uploaded_file is not None:
        if (
            not st.session_state.get("uploaded_cv")
            or st.session_state["uploaded_cv"] is None
        ):
            log_info(__name__, f"Processing uploaded cv {uploaded_file.name} ...")
            # Make a dict to store all uploaded cv data (including the cv processing outcome)
            uploaded_cv = {}
            uploaded_cv["uploaded_file"] = uploaded_file

            # PDF CV
            # Read all pdf text out
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text() or ""
            uploaded_cv["cv_text"] = cv_text

            # Get CVProcessor and analyze cv text
            cv_processor = CVProcessor()
            cv_structured_data = cv_processor.analyze_cv(cv_text)
            if not cv_structured_data:
                log_error(__name__, "Error during cv analysis.")
                st.error("Fehler beim Analysieren des Lebenslaufs.")
                return
            st.write("Extrahierte Daten:", cv_structured_data)
            uploaded_cv["cv_structured_data"] = cv_structured_data

            # Get extracted person data
            cv_person_data = cv_structured_data.get("person", {})
            st.write("Extrahierte Personendaten:", cv_person_data)
            uploaded_cv["cv_person_data"] = cv_person_data

            # Get person name
            cv_person_name = CVProcessor.get_person_name(
                cv_person_data, max_firstnames=2
            )
            st.write(cv_person_name)
            cv_candiate = cv_person_name
            uploaded_cv["cv_person_name"] = cv_person_name

            # Get soft skills
            cv_soft_skills = CVProcessor.get_all_soft_skills(cv_structured_data)
            uploaded_cv["cv_soft_skills"] = cv_soft_skills

            # Get tech skills
            cv_tech_skills = CVProcessor.get_all_tech_skills(cv_structured_data)
            uploaded_cv["cv_tech_skills"] = cv_tech_skills

            st.session_state["uploaded_cv"] = uploaded_cv
            st.success(f"CV {uploaded_file.name} is processed!")
            log_info(__name__, f"CV {uploaded_file.name} is processed!")

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

        if (
            (uploaded_cv := st.session_state.get("uploaded_cv", {}))
            and uploaded_cv.get("cv_structured_data")
            and st.button("Save")
        ):
            try:
                save_cv_logic(
                    cv_candiate=cv_candiate,
                    uploaded_cv=uploaded_cv,
                    desired_rate_min=desired_rate_min,
                    desired_rate_max=desired_rate_max,
                )
                log_info(
                    __name__, f"Committed freelancer and cv of {cv_candiate} to db."
                )
                st.success("CV skills extracted and successfully saved!")
            except Exception as e:
                log_error(__name__, f"Error saving CV: {e}")
                st.error(f"Error saving CV: {e}")
            finally:
                st.session_state["uploaded_cv"] = None


def save_cv_logic(cv_candiate, uploaded_cv, desired_rate_min, desired_rate_max):
    log_info(__name__, "Saving processed cv...")
    with session_scope() as session:
        # Freelancer
        freelancer: FreelancerModel = get_freelancer_by_name(
            name=cv_candiate, session=session
        )
        structured_data = uploaded_cv.get("cv_structured_data")
        if not structured_data:
            raise ValueError("cv_structured_data is missing.")
        contact = structured_data.get("contact")
        if not contact:
            raise ValueError("contact is missing.")
        contact_contact = contact.get("contact")
        if not contact_contact:
            raise ValueError("contact.contact is missing.")
        address = contact_contact.get("address")
        if not address:
            raise ValueError("address is missing.")
        city = contact_contact.get("city")
        if not city:
            raise ValueError("city is missing.")
        zip_code = contact_contact.get("zip-code")
        if not zip_code:
            raise ValueError("zip-code is missing.")
        country = contact_contact.get("country")
        if not country:
            # raise ValueError("country is missing.")
            country = "Deutschland"
        phone = contact_contact.get("phone")
        if not phone:
            raise ValueError("phone is missing.")
        email = contact_contact.get("email")
        if not email:
            raise ValueError("email is missing.")
        website = contact_contact.get("website")
        if not website:
            raise ValueError("website is missing.")

        if not freelancer:
            log_info(__name__, f"Adding new freelancer of {cv_candiate} to db...")
            freelancer = FreelancerModel(
                name=cv_candiate,
                soft_skills=", ".join(uploaded_cv.get("cv_soft_skills")),
                tech_skills=", ".join(uploaded_cv.get("cv_tech_skills")),
                desired_rate_min=desired_rate_min,
                desired_rate_max=desired_rate_max,
                address=address,
                city=city,
                zip_code=zip_code,
                country=country,
                phone=phone,
                email=email,
                website=website,
            )
            session.add(freelancer)
        else:
            log_info(
                __name__,
                f"Updating existing freelancer {freelancer.id} of {cv_candiate} to db.",
            )
            freelancer.soft_skills = ", ".join(uploaded_cv.get("cv_soft_skills"))
            freelancer.tech_skills = ", ".join(uploaded_cv.get("cv_tech_skills"))
            freelancer.desired_rate_min = desired_rate_min
            freelancer.desired_rate_max = desired_rate_max
            freelancer.address = address
            freelancer.city = city
            freelancer.zip_code = zip_code
            freelancer.country = country
            freelancer.phone = phone
            freelancer.email = email
            freelancer.website = website

        # CV
        cv: CVModel = get_cv_by_freelancer_id(freelancer.id, session=session)
        if cv:
            log_info(__name__, f"Existing CV found with id: {cv.id}")
        else:
            log_info(
                __name__,
                "No existing CV found for freelancer_id: {freelancer.id}",
            )
        if not cv:
            log_info(__name__, f"Adding new cv of {cv_candiate} to db...")
            cv = CVModel(
                freelancer_id=freelancer.id,
                name=cv_candiate,
                raw_text=uploaded_cv.get("cv_text"),
                structured_data=json.dumps(uploaded_cv.get("cv_structured_data")),
            )
            session.add(cv)
        else:
            log_info(__name__, f"Updating cv of {cv_candiate} to db.")
            cv.name = cv_candiate
            cv.raw_text = uploaded_cv.get("cv_text")
            cv.structured_data = json.dumps(uploaded_cv.get("cv_structured_data"))
        # Commit and Rollback are handled automatically by the contect manager
