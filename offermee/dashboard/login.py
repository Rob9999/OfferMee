from time import sleep
import streamlit as st
from offermee.dashboard.helpers.web_dashboard import (
    get_authenticator,
    is_logged_in,
    log_info,
    set_logged_in,
)
from offermee.dashboard.signup import get_title as signup_get_title
from offermee.utils.international import _T


def get_title():
    return _T("Login")


def login_render():
    st.title(get_title())
    log_info(__name__, f"Visiting page {get_title()} ...")

    # 1) Authenticator abrufen
    authenticator = get_authenticator(refresh=True)
    if authenticator is None:
        st.error("Keine Benutzerdaten gefunden. Bitte registrieren.")
        from offermee.dashboard.widgets.navigate_to import navigate_to

        navigate_to(signup_get_title())
        return

    # 2) Login-Widget anzeigen und Ergebnisse prüfen
    login_result = authenticator.login(location="main", key="login")

    # Sicherstellen, dass login_result gültig ist
    if not isinstance(login_result, (list, tuple)) or len(login_result) != 3:
        name, authentication_status, username = (
            st.session_state["name"],
            st.session_state["authentication_status"],
            st.session_state["username"],
        )
    else:
        name, authentication_status, username = login_result

    # 3) Authentifizierung prüfen
    if authentication_status is True:
        set_logged_in(True, username)
        st.session_state["logged_in"] = True
        st.success(f"Willkommen, {username}!")
        # 4) Nach erfolgreichem Login weiterleiten
        if st.button(_T("Weiter")):
            st.rerun()
    elif authentication_status is False:
        set_logged_in(False)
        st.error("Benutzername oder Passwort ist falsch.")
    else:
        st.warning("Bitte die Felder ausfüllen.")
