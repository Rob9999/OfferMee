import streamlit as st


from offermee.dashboard.helpers.web_dashboard import log_info
from offermee.dashboard.widgets.navigate_to import (
    get_default_page,
    get_pages_to_show,
)


def navigate():

    log_info(__name__, f"{get_default_page()} is default")
    st.title("OfferMee – Dashboard")
    navigator = st.navigation(get_pages_to_show(), expanded=True)
    log_info(
        __name__, f"Running '{navigator.title} - default={navigator._default}' ..."
    )
    navigator.run()


st.set_page_config(page_title="OfferMee Dashboard", layout="wide")
log_info(__name__, "Visiting page ...")
navigate()
