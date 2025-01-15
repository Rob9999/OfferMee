import streamlit as st
from offermee.dashboard.web_dashboard import is_logged_in

# Best practice: set page config at very top
st.set_page_config(page_title="OfferMee Dashboard", layout="wide")
st.title("OfferMee - Dashboard")

# Initialize session state for page selection if not present
if "page" not in st.session_state:
    st.session_state.page = None

# Define the navigation structure for logged in users
NAV_STRUCTURE = {
    "CV": {
        "CV hochladen": "CV hochladen",
        "CV bearbeiten": "CV bearbeiten",
        "CV exportieren": "CV exportieren",
        # ... additional CV-related pages
    },
    "Ausschreibungen": {
        "Online finden": "Scraper",
        "Manuelle Eingabe": "Manuelle Eingabe",
        # ... additional Ausschreibungen-related pages
    },
    "Angebote": {
        "Angebotsübersicht": "Standardangebotstemplate",
        "Projektmatcher & Angebotserstellung": "Projektmatcher & Angebotserstellung",
        "Angebotshistorie": "Angebotshistorie",
        # ... additional Angebote-related pages
    },
    "Profil": {
        "Settings": "Settings",
        # ... additional Profile-related pages
    },
    "Logout": {"Logout": "Logout"},
}

# Navigation structure for users who are not logged in
LOGGED_OUT_PAGES = {
    "": {
        "Login": "Login",
        "Sign Up": "Sign Up",
    }
}


# Build a flat list of navigation options with category prefix
def build_flat_navigation(navigation_dict):
    options = []
    page_mapping = {}
    for category, pages in navigation_dict.items():
        for page_label, page_key in pages.items():
            # Create a combined label that includes the category
            full_label = f"{category}: {page_label}"
            options.append(full_label)
            page_mapping[full_label] = page_key
    return options, page_mapping


# Function to render pages based on the page key
def render_page(page_key):
    if page_key == "Login":
        from offermee.dashboard.pages.login import render as login_render

        login_render()
    elif page_key == "Sign Up":
        from offermee.dashboard.pages.signup import render as signup_render

        signup_render()
    elif page_key == "CV hochladen":
        from offermee.dashboard.pages.cv_manager import render as cv_manager_render

        cv_manager_render()
    elif page_key == "CV bearbeiten":
        from offermee.dashboard.pages.cv_edit import render as cv_edit_render

        cv_edit_render()
    elif page_key == "CV exportieren":
        from offermee.dashboard.pages.cv_export import render as cv_export_render

        cv_export_render()
    elif page_key == "Standardangebotstemplate":
        from offermee.dashboard.pages.templates import render as templates_render

        templates_render()
    elif page_key == "Scraper":
        from offermee.dashboard.pages.scraper import render as scraper_render

        scraper_render()
    elif page_key == "Manuelle Eingabe":
        from offermee.dashboard.pages.manual_input import render as manual_input_render

        manual_input_render()
    elif page_key == "Projektmatcher & Angebotserstellung":
        from offermee.dashboard.pages.matches import render as matches_render

        matches_render()
    elif page_key == "Angebotshistorie":
        from offermee.dashboard.pages.history import render as history_render

        history_render()
    elif page_key == "Settings":
        from offermee.dashboard.pages.settings import render as settings_render

        settings_render()
    elif page_key == "Logout":
        from offermee.dashboard.pages.logout import render as logout_render

        logout_render()
    # ... add additional elif cases for other pages as needed


# Sidebar navigation based on login status
st.sidebar.header("Navigation")

if not is_logged_in():
    # For not logged in users, simple radio button navigation
    not_logged_pages = list(LOGGED_OUT_PAGES[""].keys())
    selected = st.sidebar.radio("Go to:", not_logged_pages)
    st.session_state.page = LOGGED_OUT_PAGES[""][selected]
else:
    # Build flat navigation for logged in users
    flat_options, flat_mapping = build_flat_navigation(NAV_STRUCTURE)
    # Create a single radio widget for all options
    selected_option = st.sidebar.radio("Go to:", flat_options)
    # Update session state with the corresponding page key
    st.session_state.page = flat_mapping[selected_option]

# Render the selected page if one is chosen
if st.session_state.page:
    render_page(st.session_state.page)
