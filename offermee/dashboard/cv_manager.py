import json
import traceback
from typing import Any, Dict, List
import streamlit as st

from offermee.config import Config
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.widgets.to_sreamlit import (
    create_streamlit_edit_form_from_json_schema,
)
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    log_error,
    log_info,
    join_container_path,
    stop_if_not_logged_in,
)
from offermee.database.facades.main_facades import (
    CVFacade,
    FreelancerFacade,
    ReadFacade,
)
from offermee.database.models.main_models import ContactRole
import PyPDF2

from offermee.schemas.json.schema_keys import SchemaKey
from offermee.schemas.json.schema_loader import get_schema
from offermee.dashboard.helpers.international import _T
from offermee.utils.container import Container
from offermee.utils.utils import safe_type


def cv_manager_render() -> None:
    """
    Rendert die 'Upload CV'-Page in der Streamlit-Anwendung.
    Ermöglicht das Hochladen einer PDF, das Auslesen mit AI,
    das Bearbeiten der extrahierten Daten und das Speichern in der Datenbank.
    """

    st.header(_T("Upload CV"))
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    edit_cv_form_label = _T("CV Extracted Data")

    # Kandidatenname vorbelegen (falls in local_settings hinterlegt)
    cv_candidate = st.text_input(
        label=_T("Candidate"),
        value=Config.get_instance().get_name_from_local_settings(),
    )

    path_cv_upload_root = join_container_path(page_root, "cv_upload")
    path_cv_upload_candidate = join_container_path(path_cv_upload_root, "cv_candidate")
    path_cv_upload_schema = join_container_path(path_cv_upload_root, "cv_schema")
    path_cv_upload_file = join_container_path(path_cv_upload_root, "cv_file")
    path_cv_upload_text = join_container_path(path_cv_upload_root, "cv_text")
    path_cv_edit_root = join_container_path(path_cv_upload_root, "cv_edit")
    path_cv_edit_structured_data = join_container_path(
        path_cv_edit_root, "cv_structured_data"
    )
    path_cv_edit_control = join_container_path(path_cv_edit_root, "control")

    if not container.get_value(path_cv_upload_schema, None):
        cv_schema = get_schema(SchemaKey.CV)
        container.set_value(path_cv_upload_schema, cv_schema)
        log_info(__name__, f"Set container cv schema data.")
    else:
        cv_schema = container.get_value(path_cv_upload_schema)

    container.set_value(path_cv_upload_candidate, cv_candidate)

    # Upload-Feld für PDF
    uploaded_file = st.file_uploader(_T("Upload your resume (PDF):"), type=["pdf"])

    # Nur dann ausführen, wenn eine neue Datei hochgeladen wurde
    if (
        uploaded_file
        and container.get_value(path_cv_upload_file, None) != uploaded_file
    ):
        # Workflow Section: Read out uploaded file and then process the data via AI
        log_info(__name__, f"Processing uploaded CV {uploaded_file.name} ...")
        container.set_value(path_cv_upload_file, uploaded_file)
        container.set_value(path_cv_edit_structured_data, None)

        # PDF auslesen
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text() or ""
            container.set_value(path_cv_upload_text, cv_text)
        except Exception as e:
            log_error(__name__, f"Error reading PDF: {e}")
            st.error(_T("Error reading the PDF. Please try again."))
            return

        # AI-gestützte Analyse des ausgelesenen Textes
        cv_processor = CVProcessor()
        ai_processed_cv_structured_data = cv_processor.analyze_cv(cv_text)
        if not ai_processed_cv_structured_data:
            log_error(__name__, "Error during CV analysis.")
            st.error(_T("Error analyzing the CV."))
            return
        container.set_value(
            path_cv_edit_structured_data, ai_processed_cv_structured_data
        )

    # Only if file is uplaoded and AI processed cv data is available
    if uploaded_file and container.get_value(path_cv_edit_structured_data, None):
        # Workflow Section: redit the Ai processed cv data
        create_streamlit_edit_form_from_json_schema(
            container=container,
            container_data_path=path_cv_edit_structured_data,
            container_schema_path=path_cv_upload_schema,
            container_control_path=path_cv_edit_control,
            label=edit_cv_form_label,
        )
        wantstore = container.get_value(path_cv_edit_control + ".wantstore", False)
        if wantstore:
            st.success(_T("Data Received"))
            # st.rerun()
        else:
            st.write(_T("Waiting For Data ..."))
            # st.stop()

    # Nach dem Absenden im Formular (submit) liegen die bearbeiteten Daten in st.session_state
    if container.get_value(path_cv_edit_structured_data, None) and container.get_value(
        path_cv_edit_control + ".wantstore", False
    ):
        uploaded_cv = container.get_value(path_cv_upload_root, {})
        uploaded_cv["cv_structured_data"] = container.get_value(
            path_cv_edit_structured_data
        )
        log_info(__name__, f"Preparing data of '{uploaded_file}' for saving ...")

        # Personendaten extrahieren
        cv_person_data: Dict[str, Any] = safe_type(
            uploaded_cv["cv_structured_data"], dict, {}
        ).get("person", {})
        cv_person_name = CVProcessor.get_person_name(cv_person_data, max_firstnames=2)
        st.write(
            f"{_T('CV candidate call name in offermee process')}: {cv_person_name}"
        )

        # Kandidatenname ggf. überschreiben
        cv_candidate = cv_person_name
        uploaded_cv["cv_person_name"] = cv_person_name
        uploaded_cv["firstnames"] = " ".join(cv_person_data.get("firstnames", []))
        uploaded_cv["lastname"] = cv_person_data.get("lastname", "")

        # Skills ermitteln
        cv_soft_skills = CVProcessor.get_all_soft_skills(
            uploaded_cv["cv_structured_data"]
        )
        uploaded_cv["cv_soft_skills"] = cv_soft_skills
        cv_tech_skills = CVProcessor.get_all_tech_skills(
            uploaded_cv["cv_structured_data"]
        )
        uploaded_cv["cv_tech_skills"] = cv_tech_skills

        st.success(f"{_T('CV')} {uploaded_file.name} {_T('is processed!')}")
        log_info(__name__, f"CV {uploaded_file.name} is processed!")

        # Button zum Speichern
        if uploaded_cv.get("cv_structured_data") and st.button(_T("Save")):
            try:
                save_cv_logic(
                    cv_candidate=cv_candidate,
                    uploaded_cv=uploaded_cv,
                    operator=operator,
                )
                log_info(
                    __name__, f"Committed freelancer and CV of {cv_candidate} to DB."
                )
                st.success(_T("CV skills extracted and successfully saved!"))
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                log_error(__name__, f"Error saving CV: {e}")
                st.error(f"{_T('Error saving CV')}: {e}")
            finally:
                # Session nach dem Speichern zurücksetzen
                st.session_state["uploaded_cv"] = None


def save_cv_logic(
    cv_candidate: str,
    uploaded_cv: Dict[str, Any],
    operator: str,
) -> None:
    """
    Erstellt oder aktualisiert einen Freelancer-Datensatz und den zugehörigen CV-Eintrag
    in der Datenbank.
    """
    log_info(__name__, "Saving processed CV...")

    freelancer: Dict[str, Any] = ReadFacade.get_freelancer_by_name(name=cv_candidate)
    desired_rate_min: float = uploaded_cv.get("desired_rate_min")
    safe_type(desired_rate_min, float, None, True)
    desired_rate_max: float = uploaded_cv.get("desired_rate_max")
    safe_type(desired_rate_max, float, None, True)
    structured_data: Dict[str, Any] = uploaded_cv.get("cv_structured_data")
    safe_type(structured_data, dict, None, True)

    contacts: List[Dict[str, Any]] = structured_data.get("contacts", [])
    if not contacts:
        raise ValueError("contacts is missing.")

    contact_entry = contacts[0] if contacts[0] else {}
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
        country = "Deutschland"  # Fallback

    phone = contact.get("phone")
    if not phone:
        raise ValueError("phone is missing.")

    email = contact.get("email")
    if not email:
        raise ValueError("email is missing.")

    website = contact.get("website")
    if not website:
        raise ValueError("website is missing.")

    def skills_to_db(skill_type: str, names: List[str]) -> List[Dict[str, Any]]:
        db_skills = []
        if names:
            for name in names:
                db_skills.append({"type": skill_type, "name": name})
        return db_skills

    # Freelancer anlegen, falls nicht vorhanden
    if not freelancer:
        log_info(__name__, f"Adding new freelancer {cv_candidate} to DB...")
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
            f"Updating existing freelancer {freelancer.get('id')} of {cv_candidate} to DB.",
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

    # CV aktualisieren oder anlegen
    cv = ReadFacade.get_cv_by_freelancer_id(freelancer.get("id"))
    if cv:
        log_info(__name__, f"Existing CV found with ID: {cv.get('id')}")
        log_info(__name__, f"Updating CV of {cv_candidate} in DB.")
        update_cv = {
            "name": cv_candidate,
            "cv_raw_text": uploaded_cv.get("cv_text"),
            "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
            "cv_schema_reference": json.dumps(uploaded_cv.get("cv_schema")),
        }
        CVFacade.update(record_id=cv.get("id"), data=update_cv, updated_by=operator)
    else:
        log_info(
            __name__,
            f"No existing CV found for freelancer_id: {freelancer.get('id')}, creating a new CV.",
        )
        new_cv = {
            "freelancer_id": freelancer.get("id"),
            "name": cv_candidate,
            "cv_raw_text": uploaded_cv.get("cv_text"),
            "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
            "cv_schema_reference": json.dumps(uploaded_cv.get("cv_schema")),
        }
        CVFacade.create(data=new_cv, created_by=operator)

    log_info(__name__, f"CV for {cv_candidate} has been saved successfully.")
