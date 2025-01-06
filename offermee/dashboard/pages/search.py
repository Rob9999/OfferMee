import streamlit as st

from offermee.database.db_connection import connect_to_db


def render():
    st.header("Projekte suchen")
    session = connect_to_db()

    start_date = st.date_input("Startdatum")
    location = st.text_input("Ort")
    hourly_rate = st.number_input("Max. Stundensatz", min_value=0)
    skills = st.text_input("Wunschskills (z. B. Senior AI Engineer)")

    if st.button("Suchen"):
        st.success("Suche abgeschlossen! Ergebnisse anzeigen...")
