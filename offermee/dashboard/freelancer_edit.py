import streamlit as st
from offermee.config import Config
from offermee.dashboard.widgets.db_edit import edit
from offermee.utils.international import _T
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    stop_if_not_logged_in,
)
from offermee.utils.container import Container


def get_title():
    return _T("Edit Freelancer")


def freelancer_edit_render():
    st.header(get_title())
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    edit(
        label=get_title(),
        page_root=page_root,
        container=container,
        model_name="freelancer",
        operator=operator,
    )
