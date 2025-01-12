import streamlit as st
from offermee.dashboard.web_dashboard import is_logged_in

# Best practice: set page config at very top
st.set_page_config(page_title="OfferMee Dashboard", layout="wide")
st.title("OfferMee - Dashboard")

# Initialize session state for page selection
if "page" not in st.session_state:
    st.session_state.page = "Login"

# Define possible pages when logged out
LOGGED_OUT_PAGES = [
    "Login",
    "Sign Up",
]

# Define possible pages when logged in
LOGGED_IN_PAGES = [
    "CV hinterlegen",
    "CV bearbeiten",
    "CV exportieren",
    "Standardangebotstemplate",
    "Scraper",
    "Projektsuche",
    "Projektmatcher & Angebotserstellung",
    "Angebotshistorie",
    "Settings",
    "Logout",
]


def set_valid_page(allowed_pages):
    """
    If st.session_state.page isn't in allowed_pages,
    reset it to the first allowed page to avoid ValueError
    in the st.sidebar.radio index argument.
    """
    if st.session_state.page not in allowed_pages:
        st.session_state.page = allowed_pages[0]


# Check if someone is logged in
if not is_logged_in():
    # If not logged in, allow only the 'LOGGED_OUT_PAGES' set
    set_valid_page(LOGGED_OUT_PAGES)

    page = st.sidebar.radio(
        "Gehe zu:",
        LOGGED_OUT_PAGES,
        index=LOGGED_OUT_PAGES.index(st.session_state.page),
    )
    st.session_state.page = page

    if page == "Login":
        from offermee.dashboard.pages.login import render as login_render

        login_render()

    elif page == "Sign Up":
        from offermee.dashboard.pages.signup import render as signup_render

        signup_render()

else:
    # If someone is logged in, allow the 'LOGGED_IN_PAGES' set
    set_valid_page(LOGGED_IN_PAGES)

    page = st.sidebar.radio(
        "Gehe zu:",
        LOGGED_IN_PAGES,
        index=LOGGED_IN_PAGES.index(st.session_state.page),
    )
    st.session_state.page = page

    if page == "CV hinterlegen":
        from offermee.dashboard.pages.cv_manager import render as cv_manager_render

        cv_manager_render()

    if page == "CV bearbeiten":
        from offermee.dashboard.pages.cv_edit import render as cv_edit_render

        cv_edit_render()

    if page == "CV exportieren":
        from offermee.dashboard.pages.cv_export import render as cv_export_render

        cv_export_render()

    elif page == "Standardangebotstemplate":
        from offermee.dashboard.pages.templates import render as templates_render

        templates_render()

    elif page == "Scraper":
        # Renamed import to match the label
        from offermee.dashboard.pages.scraper import render as scraper_render

        scraper_render()

    elif page == "Projektsuche":
        from offermee.dashboard.pages.search import render as search_render

        search_render()

    elif page == "Projektmatcher & Angebotserstellung":
        from offermee.dashboard.pages.matches import render as matches_render

        matches_render()

    elif page == "Angebotshistorie":
        from offermee.dashboard.pages.history import render as history_render

        history_render()

    elif page == "Settings":
        from offermee.dashboard.pages.settings import render as settings_render

        settings_render()

    elif page == "Logout":
        from offermee.dashboard.pages.logout import render as logout_render

        logout_render()
