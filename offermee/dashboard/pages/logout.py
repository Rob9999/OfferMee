import time
import streamlit as st
import os
from offermee.dashboard.web_dashboard import (
    get_authenticator,
    is_logged_in,
    set_logged_in,
)


def render():
    st.title("Logout")
    # stop_if_not_logged_in()
    if is_logged_in():
        st.warning("Möchtest du dich wirklich ausloggen?")
        authenticator = get_authenticator()
        if authenticator is None:
            st.error("Keine Benutzerdaten gefunden. Bitte registrieren.")
            set_logged_in(False)
            st.stop()
        print("LOGOUT")
        authenticator.logout(location="main", key="Logout", callback=logged_out)


def logged_out(a):
    st.session_state["logged_in"] = False
    set_logged_in(False)
    st.success("Erfolgreich ausgeloggt.")
    time.sleep(5)
    st.rerun()
