import streamlit_authenticator as stauth
import streamlit as st
from offermee.config import Config
from offermee.users.credential_loader import load_credentials_from_db
from offermee.logger import CentralLogger

web_logger = CentralLogger().getLogger(name="web")


def get_logger():
    global web_logger
    return web_logger


def log_info(page_name: str, message: str):
    global web_logger
    web_logger.info(f"{page_name} - {message}")


def log_error(page_name: str, message: str):
    global web_logger
    web_logger.error(f"{page_name} - {message}")


def start_dashboard():
    # Add dashboard logic
    pass


def get_authenticator(refresh: bool = False) -> stauth.Authenticate:
    # load current credentials from db
    credentials = load_credentials_from_db()
    if credentials is None or credentials == {} or credentials == {"usernames": {}}:
        return None  # No credentials found
    if refresh:
        st.session_state.authenticator = None
    if (
        "authenticator" not in st.session_state
        or st.session_state.authenticator is None
    ):
        # Authenticator anlegen
        st.session_state.authenticator = stauth.Authenticate(
            credentials,  # dict aus der DB
            "oe_cookie_name",  # Cookie Name
            "oe_random_salt_value",  # Irgendein geheimer/random String
            cookie_expiry_days=7,
        )
    return st.session_state.authenticator


def set_logged_in(logged_in: bool = False, username: str = None):
    web_logger.info(f"Setting logged_in to {logged_in} for {username}")
    Config.get_instance().init_current_config(logged_in=logged_in, username=username)


def is_logged_in():
    return not (
        "logged_in" not in st.session_state or st.session_state["logged_in"] != True
    )


def stop_if_not_logged_in():
    if not is_logged_in():
        st.warning("Bitte einloggen, um auf diese Seite zuzugreifen.")
        st.stop()
