import traceback
from typing import Any, Dict, List
import streamlit as st
from offermee.config import Config
from offermee.utils.international import _T
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    join_container_path,
    log_error,
    log_info,
    stop_if_not_logged_in,
)
from offermee.dashboard.widgets.selectors import render_freelancer_selection_form
from offermee.database.facades.main_facades import CVFacade, FreelancerFacade
from offermee.enums.process_status import Status
from offermee.utils.container import Container


def offer_templates_render():
    """
    1. Select a freelancer
    2. Select prefered CV of freelancer
    3. Show current offer template of freelancer
    4. Edit offer template of freelancer (apply alos a prefered CV of the freelancer)
    5. Save to db
    """
    st.header(_T("Offer Templates"))
    stop_if_not_logged_in()
    try:

        log_info(__name__, "Visiting the side.")

        page_root = __name__
        container: Container = get_app_container()
        config = Config.get_instance().get_config_data()
        email_user = config.sender_email
        operator = config.current_user

        # --- Initialize
        path_current_process = container.make_paths(
            join_container_path(page_root, "current_process"),
            typ=dict,
            exists_ok=True,
            force_typ=True,
        )
        current_process: Dict[str, Any] = container.get_value(
            path_current_process,
            {"freelancer-id": None, "cv-id": None, "status": Status.NEW},
        )
        log_info(__name__, f"current process:\n{current_process}")

        # Check if there is current process on work
        if not current_process.get("status") in [
            Status.EDIT,
            Status.ANALYZED,
            Status.VALIDATED,
        ]:
            if not current_process.get("freelancer-id") or current_process.get(
                "freelancer-id"
            ) != st.session_state.get("selected_freelancer_id"):
                # select a freelancer first
                selected_freelancer_id = render_freelancer_selection_form(
                    _T("Select to edit freelancer's offer template")
                )
                if selected_freelancer_id is None:
                    return
                current_process["freelancer-id"] = selected_freelancer_id
                current_process["status"] = Status.EDIT
                log_info(__name__, f"Selected Freelancer #{selected_freelancer_id}")
                st.rerun()

        else:  # current process on work
            log_info(
                __name__,
                f"Starting freelancer #{current_process.get('id')}'s offer template ...",
            )
            # get or create current freelancer entry
            freelancer_entry = current_process.get("freelancer")
            if freelancer_entry is None:
                freelancer_entry = {
                    "data": FreelancerFacade.get_first_by(
                        {"id": current_process.get("freelancer-id")}
                    ),
                    "cvs": CVFacade.get_all_by(
                        {"freelancer_id": current_process.get("freelancer-id")}
                    ),
                }
            # get current freelancer data
            freelancer: Dict[str, Any] = freelancer_entry.get("data", None)
            if not freelancer:
                log_error(
                    __name__,
                    f"Unknwon freelancer #{current_process.get('freelancer-id')}. You may upload a CV first!",
                )
                st.error(
                    f"{_T('Unknown freelancer')} #{current_process.get('freelancer-id')}. {_T('You may upload a CV first!')}"
                )
                st.stop()
            stored_offer_template = freelancer.get("offer_template")
            # log_debug(__name__, f"Fetched Freelancer:\n{freelancer}")
            freelancer_desired_rate = freelancer.get("desired_rate_min")
            current_process["freelance-desired-rate"] = freelancer_desired_rate
            log_info(
                __name__, f"Freelancer #{current_process.get('freelancer-id')} is found"
            )
            st.success(f"{_T('Freelancer')} {freelancer.get('name')} {_T('is found')}")

            # Template language selection (optional) # TODO
            language = st.selectbox(
                "Sprache des Templates:", options=["de", "en", "fr", "es"]
            )

            # show the html version on the bottom and the edit field at the top

            edited_offer_template = st.text_area(
                "Geben Sie Ihr Angebotstemplate ein:",
                value=stored_offer_template,
                height=300,
            )

            st.markdown("---")
            st.html(edited_offer_template)
            st.markdown("---")

            if st.button("Speichern"):
                if freelancer:
                    # freelancer["offer_template"] = template
                    FreelancerFacade.update(
                        freelancer.get("id"),
                        {"offer_template": edited_offer_template},
                    )
                    st.success("Template erfolgreich gespeichert!")
                else:
                    st.error(
                        "Freelancer-Profil nicht gefunden. Bitte hinterlegen Sie Ihren CV."
                    )
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        st.error(f"{_T('Error while work on offer templates')}: {e}")
