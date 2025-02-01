import json
import os
from typing import Any, Dict
import streamlit as st
from offermee.config import Config
from offermee.utils.international import _T
from offermee.dashboard.widgets.selectors import render_cv_selection_form
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
from offermee.database.facades.main_facades import CVFacade, SchemaFacade
from offermee.utils.container import Container


def get_title() -> str:
    return _T("Edit CV")


def cv_edit_render():
    st.header(get_title())
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    # Render the CV selection form
    render_cv_selection_form(_T("Select CV to edit"))

    # Retrieve the selected CV from session state
    selected_cv_id = st.session_state.get("selected_cv_id")

    path_cv_root = join_container_path(page_root, f"cv[{selected_cv_id}]")
    path_cv_structured_data = join_container_path(path_cv_root, "cv_structured_data")
    path_cv_schema = join_container_path(path_cv_root, "cv_schema")
    path_cv_control = join_container_path(path_cv_root, "control")

    if selected_cv_id:
        cv: Dict[str, Any] = st.session_state.get("selected_cv")
        log_info(__name__, f"Selected CV#{selected_cv_id} to edit.")
        if not container.get_value(path_cv_structured_data, None):
            structured_data, cv_schema = get_cv_data_and_schema(cv)
            if structured_data is None or cv_schema is None:
                st.info(
                    "CV nicht auswertbar. Bitte lade deinen Lebenslauf nochmals hoch."
                )
                st.stop()
            container.set_value(path_cv_structured_data, structured_data)
            container.set_value(path_cv_schema, cv_schema)
            log_info(__name__, f"Set container data.")

        ready_edited = create_streamlit_edit_form_from_json_schema(
            container=container,
            container_data_path=path_cv_structured_data,
            container_schema_path=path_cv_schema,
            container_control_path=path_cv_control,
            label=_T("CV Edit"),
        )
        log_info(__name__, f"ready: {ready_edited}")
        edited_cv = container.get_value(path_cv_structured_data)
        wants_to_store = container.get_value(path_cv_control, {}).get(
            "wantstore", False
        )
        if edited_cv and wants_to_store:
            log_info(__name__, f"Processing edited cv data ...")
            container.dump(path=Config.get_instance().get_user_temp_dir())
            # Ask to store changes
            if st.button("Speichern"):
                log_info(__name__, f"Updating CV data ...")
                CVFacade.update(
                    cv.get("id"),
                    {"cv_structured_data": json.dumps(edited_cv)},
                    operator,
                )
                st.success(_T("CV Data upadated!"))
                log_info(__name__, f"CV Data updated!")
                if st.button(_T("Procceed with CV export...")):
                    st.switch_page("pages/cv_export.py")
                else:
                    st.stop()
    else:
        st.info("Kein CV gefunden. Bitte lade zuerst deinen Lebenslauf hoch.")


def get_cv_data_and_schema(cv: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        structured_data = json.loads(cv.get("cv_structured_data"))
        if structured_data is None:
            raise ValueError("cv_structured_data is None")
        # Fetch CV Schema:
        schema_id = cv.get("cv_schema_reference_id")
        schema: Dict[str, Any] = SchemaFacade.get_by_id(schema_id)
        if not schema:
            raise ValueError(f"cv_schema_reference_id #{schema_id} is Unknown")
        cv_schema = json.loads(schema.get("schema_definition"))
        if cv_schema is None:
            raise ValueError(f"cv_schema '{schema.get('name')}' is None")
        return structured_data, cv_schema
    except Exception as e:
        log_error(__name__, "Cv data or schema reference is corrupt or None: {e}")
        return None, None
