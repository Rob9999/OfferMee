import streamlit as st
from offermee.utils.international import _T
from offermee.dashboard.cv_manager import cv_manager_render
from offermee.dashboard.cv_export import cv_export_render
from offermee.dashboard.cv_edit import cv_edit_render
from offermee.dashboard.rfp_scrap_from_email import rfp_scrap_from_email_render
from offermee.dashboard.rfp_scrap_online import rfp_scrap_online_render
from offermee.dashboard.rfp_manual_input import rfp_manual_input_render
from offermee.dashboard.rfp_view_all import rfp_view_all_render
from offermee.dashboard.offer_templates import offer_templates_render
from offermee.dashboard.offer_matches import offer_matcher_render
from offermee.dashboard.offer_view_all import offer_view_all_render
from offermee.dashboard.data_import import data_imports_render
from offermee.dashboard.settings import settings_render
from offermee.dashboard.logout import logout_render
from offermee.dashboard.signup import signup_render
from offermee.dashboard.login import login_render

from offermee.dashboard.helpers.web_dashboard import is_logged_in

st.set_page_config(page_title="OfferMee Dashboard", layout="wide")

# Title (displayed regardless of login status)
st.title("OfferMee – Dashboard")

# Example: Two different page dictionaries (logged-in vs. not logged-in users)
LOGGED_IN_PAGES = {
    _T("CV"): [
        # Each sub-page is defined here as st.Page.
        # Adjust paths to Python files if they are different.
        st.Page(cv_manager_render, title=_T("Upload CV")),
        st.Page(cv_edit_render, title=_T("Edit CV")),
        st.Page(cv_export_render, title=_T("Export CV")),
    ],
    _T("Requests For Proposal (RFPs)"): [
        st.Page(rfp_scrap_online_render, title=_T("Find Online")),
        st.Page(rfp_manual_input_render, title=_T("Manual Input")),
        st.Page(rfp_scrap_from_email_render, title=_T("Find in Email")),
        st.Page(rfp_view_all_render, title=_T("View All")),
    ],
    _T("Offers"): [
        st.Page(offer_templates_render, title=_T("Offer Templates")),
        st.Page(
            offer_matcher_render,
            title=_T("Project Matcher & Offer Creation"),
        ),
        st.Page(offer_view_all_render, title=_T("Offer History")),
    ],
    _T("Imports / Exports"): [
        st.Page(data_imports_render, title=_T("Data Imports")),
    ],
    _T("Profile"): [
        st.Page(settings_render, title=_T("Settings")),
    ],
    _T("Logout"): [
        st.Page(logout_render, title=_T("Logout")),
    ],
}

LOGGED_OUT_PAGES = {
    "": [
        # Under an empty heading (or a label of your choice)
        # we list the "not logged-in" pages.
        st.Page(login_render, title=_T("Login")),
        st.Page(signup_render, title=_T("Sign Up")),
    ]
}

# Choose the appropriate dictionary based on login status
pages_to_show = LOGGED_IN_PAGES if is_logged_in() else LOGGED_OUT_PAGES

navigator = st.navigation(pages_to_show, expanded=True)
navigator.run()
