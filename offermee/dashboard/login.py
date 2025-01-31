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

    # 1) Retrieve authenticator
    authenticator = get_authenticator(refresh=True)
    if authenticator is None:
        st.error(_T("No user data found. Please register."))
        from offermee.dashboard.widgets.navigate_to import navigate_to

        navigate_to(signup_get_title())
        return

    # 2) Display login widget and check results
    login_result = authenticator.login(location="main", key="login")

    # Ensure login_result is valid
    if not isinstance(login_result, (list, tuple)) or len(login_result) != 3:
        name, authentication_status, username = (
            st.session_state["name"],
            st.session_state["authentication_status"],
            st.session_state["username"],
        )
    else:
        name, authentication_status, username = login_result

    # 3) Check authentication
    if authentication_status is True:
        set_logged_in(True, username)
        st.session_state["logged_in"] = True
        st.success(f"Welcome, {username}!")
        # 4) Redirect after successful login
        if st.button(_T("Continue")):
            st.rerun()
    elif authentication_status is False:
        set_logged_in(False)
        st.error(_T("Username or password is incorrect."))
    else:
        st.warning(_T("Please fill in the fields."))
