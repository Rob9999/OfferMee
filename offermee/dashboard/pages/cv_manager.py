import json
import traceback
from typing import Any, Dict, List
import streamlit as st

from offermee.config import Config
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.widgets.to_sreamlit import (
    create_streamlit_edit_form_from_json_schema,
)
from offermee.dashboard.web_dashboard import log_error, log_info, stop_if_not_logged_in
from offermee.database.facades.main_facades import (
    CVFacade,
    FreelancerFacade,
    ReadFacade,
)
from offermee.database.models.main_models import ContactRole
import PyPDF2

from offermee.schemas.json.schema_keys import SchemaKey
from offermee.schemas.json.schema_loader import get_schema


def render():
    st.header("Upload CV")
    stop_if_not_logged_in()

    config = Config.get_instance()
    operator = config.get_current_user()
    cv_schema = get_schema(SchemaKey.CV)
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
            uploaded_cv["cv_schema"] = cv_schema

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

            st.write("Extrahierte Daten:")
            final_cv_structured_data = create_streamlit_edit_form_from_json_schema(
                cv_schema, cv_structured_data
            )
            uploaded_cv["cv_structured_data"] = final_cv_structured_data

            # Get extracted person data
            cv_person_data = final_cv_structured_data.get("person", {})
            # Get person name
            cv_person_name = CVProcessor.get_person_name(
                cv_person_data, max_firstnames=2
            )
            st.write(f"CV candidate call name in offermee process: {cv_person_name}")
            cv_candiate = cv_person_name
            uploaded_cv["cv_person_name"] = cv_person_name
            uploaded_cv["firstnames"] = " ".join(cv_person_data.get("firstnames"))
            uploaded_cv["lastname"] = cv_person_data.get("lastname")

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
                    cv_candidate=cv_candiate,
                    uploaded_cv=uploaded_cv,
                    desired_rate_min=desired_rate_min,
                    desired_rate_max=desired_rate_max,
                    operator=operator,
                )
                log_info(
                    __name__, f"Committed freelancer and cv of {cv_candiate} to db."
                )
                st.success("CV skills extracted and successfully saved!")
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                log_error(
                    __name__,
                    f"Error saving CV: {e}",
                )
                st.error(f"Error saving CV: {e}")
            finally:
                st.session_state["uploaded_cv"] = None


def save_cv_logic(
    cv_candidate: str,
    uploaded_cv: Dict[str, Any],
    desired_rate_min: float,
    desired_rate_max: float,
    operator: str,
):
    log_info(__name__, "Saving processed cv...")
    freelancer: Dict[str, Any] = ReadFacade.get_freelancer_by_name(name=cv_candidate)
    structured_data: Dict[str, Any] = uploaded_cv.get("cv_structured_data")
    if not structured_data:
        raise ValueError("cv_structured_data is missing.")
    contacts: List[Dict[str, Any]] = structured_data.get("contacts")
    if not contacts or len(contacts) < 1:
        raise ValueError("contacts is missing.")
    contact_entry = contacts[0] if contacts[0] else {}  # take first contact
    contact = contact_entry.get("contact")
    if not contact:
        raise ValueError("contact is missing.")
    address = contact.get("address")
    if not address:
        raise ValueError("address is missing.")
    city = contact.get("city")
    if not city:
        raise ValueError("city is missing.")
    zip_code = contact.get("zip-code")
    if not zip_code:
        raise ValueError("zip-code is missing.")
    country = contact.get("country")
    if not country:
        # raise ValueError("country is missing.")
        country = "Deutschland"
    phone = contact.get("phone")
    if not phone:
        raise ValueError("phone is missing.")
    email = contact.get("email")
    if not email:
        raise ValueError("email is missing.")
    website = contact.get("website")
    if not website:
        raise ValueError("website is missing.")

    def skills_to_db(type: str, names: list[str]):
        db_skills = []
        if names is not None:
            for name in names:
                db_skills.append({"type": type, "name": name})
        return db_skills

    if not freelancer:
        log_info(__name__, f"Adding new freelancer of {cv_candidate} to db...")
        new_freelancer = {
            "name": cv_candidate,
            "role": "DEVELOPER",
            "availability": "Sofort",
            "desired_rate_min": desired_rate_min,
            "desired_rate_max": desired_rate_max,
            "offer_template": "Standard-Template",
            "capabilities": {
                "soft_skills": skills_to_db("soft", uploaded_cv.get("cv_soft_skills")),
                "tech_skills": skills_to_db("tech", uploaded_cv.get("cv_tech_skills")),
            },
            "contact": {
                "first_name": uploaded_cv.get("firstnames"),
                "last_name": uploaded_cv.get("lastname"),
                "phone": phone,
                "email": email,
                "type": ContactRole.FREELANCER,
                "address": {
                    "street": address,
                    "city": city,
                    "zip_code": zip_code,
                    "country": country,
                },
            },
            "website": website,
        }
        freelancer = FreelancerFacade.create(data=new_freelancer, created_by=operator)
    else:
        log_info(
            __name__,
            f"Updating existing freelancer {freelancer.get('id')} of {cv_candidate} to db.",
        )
        update_freelancer = {
            "name": cv_candidate,
            "role": "DEVELOPER",
            "availability": "Sofort",
            "desired_rate_min": desired_rate_min,
            "desired_rate_max": desired_rate_max,
            "offer_template": "Standard-Template",
            "capabilities": {
                "soft_skills": skills_to_db("soft", uploaded_cv.get("cv_soft_skills")),
                "tech_skills": skills_to_db("tech", uploaded_cv.get("cv_tech_skills")),
            },
            "contact": {
                "first_name": uploaded_cv.get("firstnames"),
                "last_name": uploaded_cv.get("lastname"),
                "phone": phone,
                "email": email,
                "type": ContactRole.FREELANCER,
                "address": {
                    "street": address,
                    "city": city,
                    "zip_code": zip_code,
                    "country": country,
                },
            },
            "website": website,
        }
        FreelancerFacade.update(
            freelancer.get("id"), data=update_freelancer, updated_by=operator
        )
        # CV
        cv = ReadFacade.get_cv_by_freelancer_id(freelancer.get("id"))
        if cv:
            log_info(__name__, f"Existing CV found with id: {cv.get('id')}")
        else:
            log_info(
                __name__,
                f"No existing CV found for freelancer_id: {freelancer.get('id')}",
            )
        if not cv:
            log_info(__name__, f"Adding new cv of {cv_candidate} to db...")
            new_cv = {
                "freelancer_id": freelancer.get("id"),
                "name": cv_candidate,
                "cv_raw_text": uploaded_cv.get("cv_text"),
                "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
                "cv_schema_reference": json.dumps(uploaded_cv.get("cv_schema")),
            }
            CVFacade.create(data=new_cv, created_by=operator)
        else:
            log_info(__name__, f"Updating cv of {cv_candidate} to db.")
            update_cv = {
                "name": cv_candidate,
                "cv_raw_text": uploaded_cv.get("cv_text"),
                "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
                "cv_schema_reference": json.dumps(uploaded_cv.get("cv_schema")),
            }
            CVFacade.update(record_id=cv.get("id"), data=update_cv, updated_by=operator)
