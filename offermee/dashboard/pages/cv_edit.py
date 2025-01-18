import json
from typing import Any, Dict
import streamlit as st
from offermee.config import Config
from offermee.dashboard.widgets.to_sreamlit import (
    create_streamlit_edit_form_from_json_schema,
)
from offermee.dashboard.web_dashboard import log_error, log_info, stop_if_not_logged_in
from offermee.database.facades.main_facades import CVFacade, FreelancerFacade


def render():
    st.header("CV bearbeiten")
    stop_if_not_logged_in()

    config = Config.get_instance()
    operator = config.get_current_user()
    cv_candiate = st.text_input(
        label="Candidate", value=config.get_name_from_local_settings()
    )

    freelancer: Dict[str, Any] = FreelancerFacade.get_first_by({"name": cv_candiate})
    if not freelancer:
        st.error("Kein CV hinterlegt")
        st.stop()
    freelancer_id = freelancer.get("id")
    cv: Dict[str, Any] = CVFacade.get_first_by({"freelancer_id": freelancer_id})
    log_info(__name__, "Lade CV Daten...")
    if cv:
        structured_data, cv_schema = get_cv_data_and_schema(cv)
        if structured_data is None or cv_schema is None:
            st.info("CV nicht auswertbar. Bitte lade deinen Lebenslauf nochmals hoch.")
            st.stop()

        changed_data, submitted = create_streamlit_edit_form_from_json_schema(
            cv_schema, structured_data
        )
        log_info(__name__, f"CV Data Submitted? {submitted}:\n{changed_data}")
        if submitted:
            # Ask to store changes
            if st.button("Speichern"):
                CVFacade.update(cv.get("id"), changed_data, operator)
                st.success("CV-Daten aktualisiert!")
                if st.button("Weiter mit CV Export..."):
                    st.rerun("cv bearbeiten")
                else:
                    st.stop()
    else:
        st.info("Kein CV gefunden. Bitte lade zuerst deinen Lebenslauf hoch.")


def get_cv_data_and_schema(cv: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        structured_data = json.loads(cv.get("cv_structured_data"))
        if structured_data is None:
            raise ValueError("cv_structured_data is None")
        cv_schema = json.loads(cv.get("cv_schema_reference"))
        if cv_schema is None:
            raise ValueError("cv_schema_reference is None")
        return structured_data, cv_schema
    except Exception as e:
        log_error(__name__, "Cv data or schema reference is corrupt or None: {e}")
        return None, None
