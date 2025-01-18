from typing import Any, Callable, Dict, List, Optional
from offermee.dashboard.international import _T
import streamlit as st
from offermee.config import Config
from offermee.dashboard.web_dashboard import log_info
from offermee.dashboard.widgets.uitls import log_error
from offermee.database.facades.main_facades import CVFacade


def render_cv_selection_form(label: str, pre_selected_candidate: Optional[str] = None):
    """
    Renders a form for selecting a CV (Curriculum Vitae) with a pre-selected candidate option.

    Args:
        label (str): The title of the form.
        pre_selected_candidate (Optional[str]): The name of the pre-selected candidate.

    Returns:
        Optional[str]: The ID of the selected CV, or None if no selection is made.
    """
    with st.form(
        key=f"form_select_candidate_{label}"
    ):  # do not use a method to generate the key, submit button will not --> bug in streamlit
        st.subheader(f"{label}")

        # If no pre-selected candidate is provided, retrieve the current user
        if not pre_selected_candidate:
            try:
                config: Config = Config.get_instance()
                pre_selected_candidate = config.get_current_user()
            except Exception as e:
                log_error("Failed to retrieve current user: {}", str(e))
                st.error(_T("An error occurred while retrieving the current user."))
                st.stop()

        # Retrieve CVs from the database
        try:
            cvs: List[Dict[str, Any]] = CVFacade.get_all()
        except Exception as e:
            log_error("Failed to fetch CVs from the database: {}", str(e))
            st.error(_T("An error occurred while fetching CVs from the database."))
            st.stop()

        if not cvs:
            st.info(_T("No CVs found in the database. Please upload one first."))
            st.stop()

        # Build a list of CV data for display
        cv_table_data = []
        for cv in cvs:
            cv_table_data.append(
                {
                    "CV-ID": cv.get("id"),
                    "Freelancer-ID": cv.get("freelancer_id"),
                    "Name": cv.get("name"),
                    "Last Update": (
                        cv.get("structured_data", "")[:50] + "..."
                        if cv.get("structured_data")
                        else "<EMPTY>"
                    ),
                }
            )

        # Identify the pre-selected candidate and place it at the beginning of the list
        pre_selected_cv = next(
            (cv for cv in cv_table_data if cv["Name"] == pre_selected_candidate), None
        )
        other_cvs = [cv for cv in cv_table_data if cv["Name"] != pre_selected_candidate]
        sorted_cvs = [pre_selected_cv] + other_cvs if pre_selected_cv else other_cvs

        # Prepare options and set default selection
        options = {cv["CV-ID"]: cv for cv in sorted_cvs}
        default_value = pre_selected_cv["CV-ID"] if pre_selected_cv else None

        st.markdown(f"**{_T('Available CVs')}**")
        try:
            selected_cv_id = st.selectbox(
                _T("Select a CV:"),
                options=list(options.keys()),
                index=0 if default_value else None,
                format_func=lambda x: f"{options[x]['Name']}, CV #{x}, Freelancer #{options[x]['Freelancer-ID']}",
            )
        except Exception as e:
            log_error("Error during CV selection process: {}", str(e))
            st.error(_T("An error occurred during the CV selection process."))
            st.stop()

        if st.form_submit_button(
            _T("OK"),
            icon=":material/thumb_up:",
        ):
            log_info(__name__, f"Setting CV selection: CV#{selected_cv_id} ...")
            st.session_state["selected_cv_id"] = selected_cv_id
            st.session_state["selected_cv"] = next(
                (cv for cv in cvs if cv.get("id") == selected_cv_id), None
            )
            log_info(__name__, f"CV selection done: CV#{selected_cv_id}")
