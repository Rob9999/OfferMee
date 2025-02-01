import json
import traceback
from typing import Any, Dict, List
import streamlit as st

from offermee.config import Config
from offermee.AI.cv_processor import CVProcessor
from offermee.dashboard.widgets.db_utils import save_cv_to_db
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
import PyPDF2

from offermee.schemas.json.schema_keys import SchemaKey
from offermee.schemas.json.schema_loader import get_schema
from offermee.utils.international import _T
from offermee.utils.container import Container
from offermee.utils.utils import safe_type


def get_title() -> str:
    return _T("Upload CV")


def cv_manager_render() -> None:
    """
    Rendert die 'Upload CV'-Page in der Streamlit-Anwendung.
    Ermöglicht das Hochladen einer PDF, das Auslesen mit AI,
    das Bearbeiten der extrahierten Daten und das Speichern in der Datenbank.
    """

    st.header(get_title())
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
    path_cv_upload_schema = join_container_path(
        path_cv_upload_root, "cv_schema_reference"
    )
    path_cv_upload_file = join_container_path(path_cv_upload_root, "cv_file")
    path_cv_upload_text = join_container_path(path_cv_upload_root, "cv_raw_text")
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

        # Button zum Speichern
        if uploaded_cv.get("cv_structured_data") and st.button(_T("Save")):
            try:
                save_cv_to_db(
                    name=cv_candidate,
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
