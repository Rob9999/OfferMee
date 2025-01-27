import json
import os
from typing import Any, Dict, Optional
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from offermee.config import Config
from offermee.dashboard.widgets.selectors import render_cv_selection_form
from offermee.database.facades.main_facades import CVFacade, FreelancerFacade
from offermee.utils.international import _T
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    log_debug,
    log_error,
    log_info,
    join_container_path,
    stop_if_not_logged_in,
)
from offermee.utils.container import Container


def data_imports_render():
    """
    Render the data import page in the Streamlit dashboard.
    Allows users to import a data JSON plus JSON schema.
    """
    st.header(_T("Data Import"))
    stop_if_not_logged_in()
    # log_debug(__name__, f"Rendering data import page ...")
    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    path_data_import_root = join_container_path(page_root, "data_import")
    path_data_import_data = join_container_path(path_data_import_root, "data")
    data: Dict[str, Any] = container.get_value(path_data_import_data, {})

    # Upload-Feld für CV JSON und JSON schema
    uploaded_files = st.file_uploader(
        key="data_import_uploader",
        label=_T(
            "Upload your data as JSON and matching JSON schema (e.g. data.json, data.schema.json):"
        ),
        type=["json"],
        accept_multiple_files=True,
    )
    validatetd_data = validate_and_get_json_and_schema(uploaded_files)
    if validatetd_data:
        data.update(validatetd_data)
        container.set_value(path_data_import_data, data)
        st.session_state.data_import_uploader.clear()
    if data and len(data) > 0:
        # log_info(__name__, f"Processing uploaded data ...")

        for key in data.keys():
            with st.container(key=f"container_{key}"):
                st.markdown(f"***Data: {key}***")
                json_data = data[key]["json"]
                # st.write(json_data)
                schema = data[key]["schema"]
                # st.write(schema)
                data[key]["type"] = st.selectbox(
                    "Select data type:", ["CV", "Ausschreibung"]
                )
                if data[key].get("type") == "CV":
                    # Kandidatenname vorbelegen (falls in local_settings hinterlegt)
                    cv_candidate = st.text_input(
                        label=_T("Candidate"),
                        value=Config.get_instance().get_name_from_local_settings(),
                    )
                    # check if candidate is in database (freelancer table)
                    freelancer = FreelancerFacade.get_first_by({"name": cv_candidate})
                    if not freelancer:
                        st.warning(
                            _T(
                                "The candidate is not in the database. Shall the candidate added to the freelancers."
                            )
                        )
                    else:
                        st.success(_T("The candidate is in the database."))
                        data[key]["freelancer"] = freelancer
                        data[key]["wantstore"] = st.checkbox(
                            key=key, label=_T("Save to database"), value=False
                        )

                if data[key].get("type") and data[key].get("wantstore"):
                    if st.button(_T("Save to database")):
                        if data[key].get("type") == "CV":
                            # get freelancer_id
                            freelancer = data[key].get("freelancer")
                            new_cv = {
                                "freelancer_id": freelancer.get("id"),
                                "name": cv_candidate,
                                "cv_raw_text": ("data import"),
                                "cv_structured_data": json.dumps(data[key]["json"]),
                                "cv_schema_reference": json.dumps(data[key]["schema"]),
                            }
                            CVFacade.create(new_cv, operator)
                            # data.pop(key)
                            log_info(__name__, f"CV Data '{key}' saved to database.")
                # log_info(__name__, f"Viewing data '{key}'.")
        # Redirect to CV edit page
        st.rerun()


def validate_and_get_json_and_schema(
    uploaded_files: list[UploadedFile],
) -> Optional[Dict[str, Any]]:
    # log_debug(__name__, f"Validating uploaded files ...")
    if not uploaded_files:
        st.info(
            _T(
                "Please upload a JSON file containeing the data and its matching JSON schema file."
            )
        )
        return None
    data = {}
    for uploaded_file in uploaded_files:
        if not uploaded_file.name.endswith(".json") and not uploaded_file.name.endswith(
            ".schema.json"
        ):
            st.info(
                _T("Please upload only JSON file and its matching JSON schema file.")
            )
            return None
        # check if a JSON data file and its matching JSON schema file are uploaded (data,josn and data.schema.json)
        # ectract filename and check if the other file is also uploaded
        file_name = str(uploaded_file.name.split(".")[0])
        if data.get(file_name) is None:
            data[file_name] = {}
        if uploaded_file.name.endswith(".schema.json"):
            schema = json.loads(uploaded_file.read())
            data[file_name]["schema"] = schema
        elif uploaded_file.name.endswith(".json"):
            json_data = json.loads(uploaded_file.read())
            data[file_name]["json"] = json_data
    # validate if both files are uploaded
    for key in data.keys():
        if "schema" not in data[key]:
            st.info(
                _T(
                    f"Missing '{key}.schema.json' of '{key}'.\nPlease upload both JSON file and its matching JSON schema file."
                )
            )
            return None
        if "json" not in data[key]:
            st.info(
                _T(
                    f"Missing '{key}.json' of '{key}'.\n Please upload both JSON file and its matching JSON schema file."
                )
            )
            return None
    return data
