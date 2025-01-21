import streamlit as st
from offermee.dashboard.helpers.international import _T
from offermee.dashboard.cv_manager import cv_manager_render
from offermee.dashboard.cv_export import cv_export_render
from offermee.dashboard.cv_edit import cv_edit_render
from offermee.dashboard.scraper import scraper_render
from offermee.dashboard.manual_input import manual_input_render
from offermee.dashboard.templates import templates_render
from offermee.dashboard.matches import matches_render
from offermee.dashboard.history import history_render
from offermee.dashboard.settings import settings_render
from offermee.dashboard.logout import logout_render
from offermee.dashboard.signup import signup_render
from offermee.dashboard.login import login_render

from offermee.dashboard.helpers.web_dashboard import is_logged_in

st.set_page_config(page_title="OfferMee Dashboard", layout="wide")

# Titel (wird unabhängig vom Login-Status angezeigt)
st.title("OfferMee – Dashboard")

# Beispiel: Zwei unterschiedliche Page-Dictionaries (eingeloggte vs. nicht eingeloggte Nutzer)
LOGGED_IN_PAGES = {
    _T("CV"): [
        # Jede Sub-Seite wird hier als st.Page definiert.
        # Pfade zu den Python-Dateien anpassen, falls sie anders lauten.
        st.Page(cv_manager_render, title=_T("CV hochladen")),
        st.Page(cv_edit_render, title=_T("CV bearbeiten")),
        st.Page(cv_export_render, title=_T("CV exportieren")),
    ],
    _T("Ausschreibungen"): [
        st.Page(scraper_render, title=_T("Online finden")),
        st.Page(manual_input_render, title=_T("Manuelle Eingabe")),
    ],
    _T("Angebote"): [
        st.Page(templates_render, title=_T("Angebotsübersicht")),
        st.Page(
            matches_render,
            title=_T("Projektmatcher & Angebotserstellung"),
        ),
        st.Page(history_render, title=_T("Angebotshistorie")),
    ],
    _T("Profil"): [
        st.Page(settings_render, title=_T("Settings")),
    ],
    _T("Logout"): [
        st.Page(logout_render, title=_T("Logout")),
    ],
}

LOGGED_OUT_PAGES = {
    "": [
        # Unter einer leeren Überschrift (oder einem Label deiner Wahl)
        # listen wir die „Nicht-logged-in“-Seiten.
        st.Page(login_render, title=_T("Login")),
        st.Page(signup_render, title=_T("Sign Up")),
    ]
}

# Wähle anhand des Login-Status das passende Dictionary aus
pages_to_show = LOGGED_IN_PAGES if is_logged_in() else LOGGED_OUT_PAGES

navigator = st.navigation(pages_to_show, expanded=True)
navigator.run()
