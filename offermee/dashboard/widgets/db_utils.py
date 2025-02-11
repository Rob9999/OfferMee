from offermee.enums.process_status import Status
from offermee.utils.international import _T
import json
from typing import Any, Dict, List
import streamlit as st
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.helpers.web_dashboard import log_error, log_info
from offermee.database.facades.main_facades import (
    CVFacade,
    FreelancerFacade,
    RFPFacade,
    ReadFacade,
    SchemaFacade,
)
from offermee.database.models.main_models import ContactRole, RFPSource
from offermee.utils.utils import safe_type


def save_cv_to_db(
    name: str,
    uploaded_cv: Dict[str, Any],
    operator: str,
) -> None:
    """
    Erstellt oder aktualisiert einen Freelancer-Datensatz und den zugehörigen CV-Eintrag
    in der Datenbank.

    name:   str with (max 2) firstnames and the lastname of the candidate; e.g. Firstname1 Firstname2 Lastname.
            If None then the name of the cv will be extracted to be the candidate's name (for FreelancerModel and CVModel)
    uploaded_cv: {
        "desired_rate_min": float with the min rate,
        "desired_rate_max": float with the max rate,
        "cv_structured_data": dict with the cv data according to the cv.schema.json,
        "cv_schema_reference": dict with the cv.schema.json,
        "cv_raw_text": str with the cv raw text,
    }
    operator: str with the operator name
    """
    log_info(__name__, "Saving processed CV...")

    # Personendaten extrahieren
    cv_person_data: Dict[str, Any] = safe_type(
        uploaded_cv["cv_structured_data"], dict, {}
    ).get("person", {})
    cv_person_name = CVProcessor.get_person_name(cv_person_data, max_firstnames=2)
    st.write(f"{_T('CV candidate call name in offermee process')}: {cv_person_name}")
    # Kandidatenname ggf. überschreiben
    name = name if name else cv_person_name
    uploaded_cv["cv_person_name"] = cv_person_name
    uploaded_cv["firstnames"] = " ".join(cv_person_data.get("firstnames", []))
    uploaded_cv["lastname"] = cv_person_data.get("lastname", "")
    # Skills ermitteln
    cv_soft_skills = CVProcessor.get_all_soft_skills(uploaded_cv["cv_structured_data"])
    uploaded_cv["cv_soft_skills"] = cv_soft_skills
    cv_tech_skills = CVProcessor.get_all_tech_skills(uploaded_cv["cv_structured_data"])
    uploaded_cv["cv_tech_skills"] = cv_tech_skills
    st.success(f"{_T('CV')} {name} {_T('is processed!')}")
    log_info(__name__, f"CV {name} is processed!")

    freelancer: Dict[str, Any] = ReadFacade.get_freelancer_by_name(name=name)
    desired_rate_min: float = uploaded_cv.get("desired_rate_min")
    safe_type(desired_rate_min, float, None, False)
    desired_rate_max: float = uploaded_cv.get("desired_rate_max")
    safe_type(desired_rate_max, float, None, False)
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
        log_info(__name__, f"Adding new freelancer {name} to DB...")
        new_freelancer = {
            "name": name,
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
            f"Updating existing freelancer {freelancer.get('id')} of {name} to DB.",
        )
        update_freelancer = {
            "name": name,
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
    # Fetch or Create CV Schema:
    schema_definition = uploaded_cv.get("cv_schema_reference")
    schema: Dict[str, Any] = SchemaFacade.get_first_by(
        {"schema_definition": schema_definition},
    )
    if not schema:
        schema: Dict[str, Any] = SchemaFacade.create(
            {
                "name": "cv.schema.json",
                "schema_definition": schema_definition,
                "description": "JSON Schema of Structured CV Data.",
            },
        )
    # CV aktualisieren oder anlegen
    cv = ReadFacade.get_cv_by_freelancer_id(freelancer.get("id"))
    if cv:
        log_info(__name__, f"Existing CV found with ID: {cv.get('id')}")
        log_info(__name__, f"Updating CV of {name} in DB.")
        update_cv = {
            "name": name,
            "cv_raw_text": uploaded_cv.get("cv_raw_text"),
            "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
            "cv_schema_reference_id": schema.get("id"),
        }
        CVFacade.update(record_id=cv.get("id"), data=update_cv, updated_by=operator)
    else:
        log_info(
            __name__,
            f"No existing CV found for freelancer_id: {freelancer.get('id')}, creating a new CV.",
        )
        new_cv = {
            "freelancer_id": freelancer.get("id"),
            "name": name,
            "cv_raw_text": uploaded_cv.get("cv_raw_text"),
            "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
            "cv_schema_reference_id": schema.get("id"),
        }
        CVFacade.create(data=new_cv, created_by=operator)

    log_info(__name__, f"CV for {name} has been saved successfully.")


def save_to_db(
    rfp_entry: Dict[str, Any],
    allow_updating: bool = False,
    operator: str = "system",
):
    try:
        if not rfp_entry:
            raise ValueError("Missing RFP Entry")
        if not operator:
            raise ValueError("Missing Operator")
        final_data: Dict[str, Any] = rfp_entry.get("data")
        if not final_data:
            raise ValueError("Missing RFP Data")
        rfp: Dict[str, Any] = final_data.get("project")
        if not rfp:
            raise ValueError("Missing RFP")
        source = rfp.get("source")
        if not source:
            raise ValueError(f"Missing RFP Source, see {RFPSource}")
        rfp_record = ReadFacade.get_source_rule_unique_rfp_record(
            source=source,
            contact_person_email=rfp.get("contact-person-email"),
            title=rfp.get("title"),
            original_link=rfp.get("orginal_link"),
            provider=rfp.get("provider"),
        )
        update_record: bool = False
        if rfp_record:
            st.warning(
                f"{_T('Similar RFP already exists')}: '{rfp.get('source')}', '{rfp.get('title')}', '{rfp.get('contact-person-email')}', '{rfp.get('provider')}', '{rfp.get('orginal_link')}'."
            )
            update_record = st.checkbox(
                _T("Update Record"),
                key=f"Update_RFP_Record_#{rfp_record.get('id')}",
                value=allow_updating,
                disabled=not allow_updating,
            )
            return
        if update_record:
            RFPFacade.update(
                record_id=rfp_record.get("id"),
                data=rfp,
                updated_by=operator,
            )
        else:
            RFPFacade.create(
                data=rfp,
                created_by=operator,
            )
        rfp_entry["status"] = Status.SAVED
        st.success(f"{_T('Saved RFP')}: '{rfp.get('title')}'.")
    except Exception as e:
        log_error(__name__, f"ERROR saving to DB: {e}")
        st.error(f"{_T('ERROR while saving')}: {e}")
