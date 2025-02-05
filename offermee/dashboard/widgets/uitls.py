import traceback
from typing import Optional
import streamlit as st
from offermee.utils.logger import CentralLogger
from offermee.utils.container import Container

key_number = 0


def get_valid_next_key():
    global key_number
    key_number += 1
    return f"_{key_number}"


widget_logger = CentralLogger.getLogger("widget")


def log_info(msg: object, *args: object):
    global widget_logger
    if args:
        widget_logger.info(msg, *args)
    else:
        widget_logger.info(msg)


def log_warning(msg: object, *args: object):
    global widget_logger
    if args:
        widget_logger.warning(msg, *args)
    else:
        widget_logger.warning(msg)


def log_error(msg: object, *args: object):
    global widget_logger
    if args:
        widget_logger.error(msg, *args)
    else:
        widget_logger.error(msg)


def create_session_container(container_label: str) -> Optional[Container]:
    try:
        if container_label in st.session_state:
            log_warning(f"Overwriting session container '{container_label}'.")
        else:
            log_info(f"Creating session container '{container_label}'.")
        container = Container(name=container_label)
        st.session_state[container_label] = container
        return container
    except Exception as e:
        log_error(f"Error creating session container '{container_label}': {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        return None


def get_or_create_session_container(container_label: str) -> Optional[Container]:
    try:
        if container_label not in st.session_state:
            return create_session_container(container_label=container_label)
        else:
            log_info(f"Getting session container '{container_label}'.")
            return st.session_state[container_label]
    except Exception as e:
        log_error(
            f"Error getting or creating session container '{container_label}': {e}"
        )
        traceback.print_exception(type(e), e, e.__traceback__)
        return None


def has_session_container(container_label: str) -> Optional[bool]:
    if container_label in st.session_state:
        return True
    return False


def del_session_container(container_label: str) -> Optional[bool]:
    try:
        if not has_session_container:
            log_warning(
                f"Session container '{container_label}' is already deleted or was not created."
            )
            return False
        del st.session_state[container_label]
        log_info(f"Session container '{container_label}' deleted.")
        return True
    except Exception as e:
        log_error(f"Error deleting session container '{container_label}': {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        return None
