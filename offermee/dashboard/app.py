import streamlit as st

st.set_page_config(page_title="OfferMee Dashboard", layout="wide")

st.title("OfferMee - Dashboard")
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Gehe zu:",
    [
        "CV hinterlegen",
        "Standardangebotstemplate",
        "Scrapper",
        "Projektsuche",
        "Projektübersicht",
        "Angebotshistorie",
    ],
)

if page == "CV hinterlegen":
    from offermee.dashboard.pages.cv_manager import render as cv_manager_render

    cv_manager_render()

elif page == "Standardangebotstemplate":
    from offermee.dashboard.pages.templates import render as templates_render

    templates_render()

elif page == "Projektsuche":
    from offermee.dashboard.pages.search import render as search_render

    search_render()

elif page == "Scrapper":
    from offermee.dashboard.pages.scraper import render as scrapper_render

    scrapper_render()

elif page == "Projektübersicht":
    from offermee.dashboard.pages.matches import render as matches_render

    matches_render()

elif page == "Angebotshistorie":
    from offermee.dashboard.pages.history import render as history_render

    history_render()
