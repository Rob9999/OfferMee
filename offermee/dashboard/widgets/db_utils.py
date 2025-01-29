from offermee.utils.international import _T
import json
from typing import Any, Dict, List
import streamlit as st
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.helpers.web_dashboard import log_info
from offermee.database.facades.main_facades import (
    CVFacade,
    FreelancerFacade,
    ReadFacade,
)
from offermee.database.models.main_models import ContactRole
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

    # CV aktualisieren oder anlegen
    cv = ReadFacade.get_cv_by_freelancer_id(freelancer.get("id"))
    if cv:
        log_info(__name__, f"Existing CV found with ID: {cv.get('id')}")
        log_info(__name__, f"Updating CV of {name} in DB.")
        update_cv = {
            "name": name,
            "cv_raw_text": uploaded_cv.get("cv_raw_text"),
            "cv_structured_data": json.dumps(uploaded_cv.get("cv_structured_data")),
            "cv_schema_reference": json.dumps(uploaded_cv.get("cv_schema_reference")),
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
            "cv_schema_reference": json.dumps(uploaded_cv.get("cv_schema_reference")),
        }
        CVFacade.create(data=new_cv, created_by=operator)

    log_info(__name__, f"CV for {name} has been saved successfully.")
