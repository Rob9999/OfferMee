import streamlit_authenticator as stauth
import streamlit as st
from offermee.utils.config import Config
from offermee.dashboard.widgets.uitls import (
    del_session_container,
    get_or_create_session_container,
    has_session_container,
)
from offermee.users.credential_loader import load_credentials_from_db
from offermee.utils.logger import CentralLogger
from offermee.utils.container import Container

g_web_logger = CentralLogger.getLogger(name="web")
g_app_name = "Offermee"
g_app_container = None


def get_logger():
    global g_web_logger
    return g_web_logger


def log_debug(page_name: str, message: str):
    global g_web_logger
    g_web_logger.debug(f"{page_name} - {message}")


def log_info(page_name: str, message: str):
    global g_web_logger
    g_web_logger.info(f"{page_name} - {message}")


def log_warning(page_name: str, message: str):
    global g_web_logger
    g_web_logger.warning(f"{page_name} - {message}")


def log_error(page_name: str, message: str):
    global g_web_logger
    g_web_logger.error(f"{page_name} - {message}")


def start_dashboard(app_name: str) -> Container:
    # Dashboard logic
    global g_app_name
    g_app_name = app_name
    global g_app_container
    g_app_container = get_app_container()
    log_info(__name__, f"Starting {g_app_name} dashboard.")
    return g_app_container


def get_app_container() -> Container:
    global g_app_container
    if g_app_container is None:
        g_app_container = get_or_create_session_container(
            container_label=g_app_name + "_container"
        )
    return g_app_container


def get_app_name() -> str:
    return g_app_name


def join_container_path(*args):
    return ".".join(args)


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
    g_web_logger.info(f"Setting logged_in to {logged_in} for {username}")
    Config.get_instance().init_current_config(logged_in=logged_in, username=username)
    # Dashboard logic
    global g_app_container
    if has_session_container(g_app_name + "_container"):
        del_session_container(g_app_name + "_container")
    if logged_in:
        g_app_container = get_app_container()
    else:
        g_app_container = None


def is_logged_in():
    return not (
        "logged_in" not in st.session_state or st.session_state["logged_in"] != True
    )


def stop_if_not_logged_in():
    if not is_logged_in():
        st.warning("Bitte einloggen, um auf diese Seite zuzugreifen.")
        st.stop()
