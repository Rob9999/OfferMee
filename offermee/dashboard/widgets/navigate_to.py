from time import sleep
import streamlit as st
from streamlit.runtime.scriptrunner_utils.script_run_context import (
    ScriptRunContext,
    get_script_run_ctx,
)
from offermee.dashboard.freelancer_edit import (
    freelancer_edit_render,
    get_title as freelancer_edit_get_title,
)
from offermee.dashboard.freelancer_view_all import (
    freelancer_view_all_render,
    get_title as freelancer_view_all_get_title,
)
from offermee.dashboard.helpers.web_dashboard import is_logged_in, log_info
from offermee.utils.international import _T
from offermee.dashboard.cv_manager import (
    cv_manager_render,
    get_title as cv_manager_get_title,
)
from offermee.dashboard.cv_export import (
    cv_export_render,
    get_title as cv_export_get_title,
)
from offermee.dashboard.cv_edit import cv_edit_render, get_title as cv_edit_get_title
from offermee.dashboard.cv_view_all import (
    cv_view_all_render,
    get_title as cv_view_all_get_title,
)
from offermee.dashboard.rfp_scrap_from_email import (
    rfp_scrap_from_email_render,
    get_title as rfp_scrap_from_email_get_title,
)
from offermee.dashboard.rfp_scrap_online import (
    rfp_scrap_online_render,
    get_title as rfp_scrap_online_get_title,
)
from offermee.dashboard.rfp_manual_input import (
    rfp_manual_input_render,
    get_title as rfp_manual_input_get_title,
)
from offermee.dashboard.rfp_view_all import (
    rfp_view_all_render,
    get_title as rfp_view_all_get_title,
)
from offermee.dashboard.offer_templates import (
    offer_templates_render,
    get_title as offer_templates_get_title,
)
from offermee.dashboard.offer_matches import (
    offer_matcher_render,
    get_title as offer_matcher_get_title,
)
from offermee.dashboard.offer_view_all import (
    offer_view_all_render,
    get_title as offer_view_all_get_title,
)
from offermee.dashboard.data_import import (
    data_imports_render,
    get_title as data_imports_get_title,
)
from offermee.dashboard.settings import settings_render, get_title as settings_get_title
from offermee.dashboard.logout import logout_render, get_title as logout_get_title
from offermee.dashboard.signup import signup_render, get_title as signup_get_title
from offermee.dashboard.login import login_render, get_title as login_get_title

LOGGED_IN_PAGES = {
    _T("CV"): [
        st.Page(
            cv_manager_render,
            title=cv_manager_get_title(),
            icon=":material/account_box:",
        ),
        st.Page(
            cv_edit_render,
            title=cv_edit_get_title(),
            icon=":material/edit:",
        ),
        st.Page(
            cv_export_render,
            title=cv_export_get_title(),
            icon=":material/file_download:",
        ),
        st.Page(
            cv_view_all_render,
            title=cv_view_all_get_title(),
            icon=":material/view_list:",
        ),
    ],
    _T("Freelancers"): [
        st.Page(
            freelancer_edit_render,
            title=freelancer_edit_get_title(),
            icon=":material/group:",
        ),
        st.Page(
            freelancer_view_all_render,
            title=freelancer_view_all_get_title(),
            icon=":material/view_list:",
        ),
    ],
    _T("Requests For Proposal (RFPs)"): [
        st.Page(
            rfp_scrap_online_render,
            title=rfp_scrap_online_get_title(),
            icon=":material/search:",
        ),
        st.Page(
            rfp_manual_input_render,
            title=rfp_manual_input_get_title(),
            icon=":material/input:",
        ),
        st.Page(
            rfp_scrap_from_email_render,
            title=rfp_scrap_from_email_get_title(),
            icon=":material/email:",
        ),
        st.Page(
            rfp_view_all_render,
            title=rfp_view_all_get_title(),
            icon=":material/view_list:",
        ),
    ],
    _T("Offers"): [
        st.Page(
            offer_templates_render,
            title=offer_templates_get_title(),
            icon=":material/description:",
        ),
        st.Page(
            offer_matcher_render,
            title=offer_matcher_get_title(),
            icon=":material/compare_arrows:",
        ),
        st.Page(
            offer_view_all_render,
            title=offer_view_all_get_title(),
            icon=":material/history:",
        ),
    ],
    _T("Imports / Exports"): [
        st.Page(
            data_imports_render,
            title=data_imports_get_title(),
            icon=":material/import_export:",
        ),
    ],
    _T("Profile"): [
        st.Page(
            settings_render,
            title=settings_get_title(),
            icon=":material/settings:",
        ),
    ],
    _T("Logout"): [
        st.Page(
            logout_render,
            title=logout_get_title(),
            icon=":material/logout:",
        ),
    ],
}
LOGGED_OUT_PAGES = {
    "": [
        # Under an empty heading we list the "not logged-in" pages.
        st.Page(
            login_render,
            title=login_get_title(),
            icon=":material/login:",
        ),
        st.Page(
            signup_render,
            title=signup_get_title(),
            icon=":material/app_registration:",
        ),
    ]
}


def get_pages_to_show():
    # Choose the appropriate dictionary based on login status
    return LOGGED_IN_PAGES if is_logged_in() else LOGGED_OUT_PAGES


def set_default_page(default_page_title: str = None):
    default_page = None
    for _, section in get_pages_to_show().items():
        for page in section:
            is_default = True if page._title == default_page_title else False
            page._default = is_default
            if is_default:
                log_info(__name__, f"Set page '{page._title}' as default.")
                default_page = page
    if default_page and default_page._can_be_called == False:
        ctx = get_script_run_ctx()
        if not ctx:
            default_page._can_be_called = True
            default_page.run()
        else:
            ctx.pages_manager.set_script_intent(
                page_script_hash=default_page._script_hash, page_name=default_page.title
            )
            ctx.set_mpa_v2_page(default_page._script_hash)
    st.rerun()


def get_default_page() -> str:
    for _, section in LOGGED_OUT_PAGES.items():
        for page in section:
            if page._default:
                return page._title
    return None


def navigate_to(page_title: str = None, wait_time: int = 3):
    def get_text():
        return f"{_T('Navigating to')} ***{page_title}***: {abs(wait_time):.2f} {_T('seconds')} ..."

    if isinstance(wait_time, int):
        wait_time = float(wait_time)
    if not wait_time or wait_time < 0:
        wait_time = 0.0
    all_time = wait_time
    with st.container(border=True):
        # count down
        progress_bar = st.progress(0, text=get_text())
        while wait_time > 0:
            sleep(0.1)
            wait_time -= 0.1
            progress_bar.progress(
                value=(all_time - wait_time) / all_time,
                text=get_text(),
            )
    # set page
    set_default_page(page_title)
