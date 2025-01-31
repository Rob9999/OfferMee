import streamlit as st
from offermee.users.user_management import register_user
from offermee.utils.international import _T


def get_title() -> str:
    return _T("Sign Up")


def signup_render():
    st.title(get_title())

    username = st.text_input("Username")
    email = st.text_input("Email (optional)")
    password = st.text_input("Passwort", type="password")
    if st.button("Jetzt registrieren"):
        ok, msg = register_user(username, password, email)
        if ok:
            st.success(msg)
            from offermee.dashboard.widgets.navigate_to import navigate_to
            from offermee.dashboard.login import get_title as login_get_title

            st.button(
                _T("Weiter"),
                on_click=navigate_to,
                args=(login_get_title(), 3),
            )

        else:
            st.error(msg)
