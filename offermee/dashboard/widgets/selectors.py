from typing import Any, Callable, Dict, List, Optional
from offermee.dashboard.helpers.international import _T
import streamlit as st
from offermee.config import Config
from offermee.dashboard.helpers.web_dashboard import log_info
from offermee.dashboard.widgets.uitls import log_error
from offermee.database.facades.main_facades import CVFacade, FreelancerFacade


def render_cv_selection_form(label: str, pre_selected_candidate: Optional[str] = None):
    """
    Renders a form for selecting a CV (Curriculum Vitae) with a pre-selected candidate option.

    Args:
        label (str): The title of the form.
        pre_selected_candidate (Optional[str]): The name of the pre-selected candidate. Defaults to None. If None is provided, the current user's local settings name will be used.

    Returns:
        Optional[str]: The ID of the selected CV, or None if no selection is made.
    """
    log_info(
        __name__,
        f"Rendering CV selection form for '{label}' and pre_selected_candidate '{pre_selected_candidate}' ...",
    )
    with st.form(
        key=f"form_select_candidate_{label}"
    ):  # do not use a method to generate the key, submit button will not --> bug in streamlit
        st.subheader(f"{label}")

        # If no pre-selected candidate is provided, retrieve the current user's local settings name from the local settings
        if not pre_selected_candidate:
            try:
                config: Config = Config.get_instance()
                pre_selected_candidate = config.get_name_from_local_settings()
            except Exception as e:
                log_error(
                    "Failed to retrieve current user's local settings name: {}", str(e)
                )
                st.error(
                    _T(
                        "An error occurred while retrieving the current user's local settings name."
                    )
                )
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

        # Prepare options and set default selection
        options = {cv["CV-ID"]: cv for cv in cv_table_data}
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


def render_freelancer_selection_form(
    label: str, pre_selected_candidate: Optional[str] = None
):
    """
    Renders a form for selecting a freelancer with a pre-selected candidate option.

    Args:
        label (str): The title of the form.
        pre_selected_candidate (Optional[str]): The name of the pre-selected candidate. Defaults to None. If None is provided, the current user's local settings name will be used.

    Returns:
        Optional[str]: The ID of the selected freelancer, or None if no selection is made.
    """
    log_info(
        __name__,
        f"Rendering freelancer selection form for '{label}' and pre_selected_candidate '{pre_selected_candidate}' ...",
    )
    with st.form(
        key=f"form_select_candidate_{label}"
    ):  # do not use a method to generate the key, submit button will not --> bug in streamlit
        st.subheader(f"{label}")

        # If no pre-selected candidate is provided, retrieve the current user's local settings name from the local settings
        if not pre_selected_candidate:
            try:
                config: Config = Config.get_instance()
                pre_selected_candidate = config.get_name_from_local_settings()
            except Exception as e:
                log_error(
                    "Failed to retrieve current user's local settings name: {}", str(e)
                )
                st.error(
                    _T(
                        "An error occurred while retrieving the current user's local settings name."
                    )
                )
                st.stop()

        # Retrieve freelancers from the database
        try:
            freelancers: List[Dict[str, Any]] = FreelancerFacade.get_all()
        except Exception as e:
            log_error("Failed to fetch freelancers from the database: {}", str(e))
            st.error(
                _T("An error occurred while fetching freelancers from the database.")
            )
            st.stop()

        if not freelancers:
            st.info(_T("No freelancers found in the database. Please upload CV first."))
            st.stop()

        # Build a list of CV data for display
        freelancer_table_data = []
        for freelancer in freelancers:
            freelancer_table_data.append(
                {
                    "ID": freelancer.get("id"),
                    "Name": freelancer.get("name"),
                    "Availability": freelancer.get("availability"),
                    "Role": freelancer.get("role"),
                }
            )

        # Identify the pre-selected candidate and place it at the beginning of the list
        pre_selected_freelancer = next(
            (
                cv
                for cv in freelancer_table_data
                if cv["Name"] == pre_selected_candidate
            ),
            None,
        )

        # Prepare options and set default selection
        options = {freelancer["ID"]: freelancer for freelancer in freelancer_table_data}
        default_value = (
            pre_selected_freelancer["ID"] if pre_selected_freelancer else None
        )

        st.markdown(f"**{_T('Available Freelancers')}**")
        try:
            selected_freelancer_id = st.selectbox(
                _T("Select a Freelancer:"),
                options=list(options.keys()),
                index=0 if default_value else None,
                format_func=lambda x: f"{options[x]['Name']}, #{x}, {_T('Availability')} {options[x]['Availability']}, {_T('Role')} {options[x]['Role']}",
            )
        except Exception as e:
            log_error("Error during freelancer selection process: {}", str(e))
            st.error(_T("An error occurred during the freelancer selection process."))
            st.stop()

        if st.form_submit_button(
            _T("OK"),
            icon=":material/thumb_up:",
        ):
            log_info(
                __name__, f"Setting freelancer selection: #{selected_freelancer_id} ..."
            )
            st.session_state["selected_freelancer_id"] = selected_freelancer_id
            st.session_state["selected_freelancer"] = next(
                (
                    freelancer
                    for freelancer in freelancers
                    if freelancer.get("id") == selected_freelancer_id
                ),
                None,
            )
            log_info(__name__, f"Freelancer selection done: #{selected_freelancer_id}")
            return selected_freelancer_id
        return None
