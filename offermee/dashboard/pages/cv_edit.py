from typing import Any, Dict
import streamlit as st
from offermee.config import Config
from offermee.dashboard.transformers.to_sreamlit import (
    create_streamlit_form_from_json_schema,
)
from offermee.dashboard.web_dashboard import stop_if_not_logged_in
from offermee.database.db_connection import connect_to_db
from offermee.database.facades.main_facades import CVFacade, FreelancerFacade
from offermee.schemas.json.schema_keys import SchemaKey
from offermee.schemas.json.schema_loader import get_schema


def render():
    st.header("CV bearbeiten")
    stop_if_not_logged_in()

    config = Config.get_instance()
    operator = config.get_current_user()
    cv_schema = get_schema(SchemaKey.CV)
    cv_candiate = st.text_input(
        label="Candidate", value=config.get_name_from_local_settings()
    )

    freelancer: Dict[str, Any] = FreelancerFacade.get_first_by(name=cv_candiate)
    if not freelancer:
        st.error("Kein CV hinterlegt")
        st.stop()
    freelancer_id = freelancer.id
    cv: Dict[str, Any] = CVFacade.get_first_by(freelancer_id=freelancer_id)

    if cv:
        structured_data = cv.cv_structured_data

        changed_data = create_streamlit_form_from_json_schema(
            cv_schema, structured_data
        )

        # Ask to store changes
        if st.button("Speichern"):
            CVFacade.update(cv.get("id"), changed_data, operator)
            st.success("CV-Daten aktualisiert!")
    else:
        st.info("Kein CV gefunden. Bitte lade zuerst deinen Lebenslauf hoch.")
