import streamlit as st
from offermee.config import Config
from offermee.dashboard.web_dashboard import stop_if_not_logged_in
from offermee.database.db_connection import connect_to_db, get_freelancer_by_name
from offermee.database.models.cv_model import CVModel
from offermee.database.models.freelancer_model import FreelancerModel


def render():
    st.header("CV bearbeiten")
    stop_if_not_logged_in()

    config = Config.get_instance()
    cv_candiate = st.text_input(
        label="Candiate", value=config.get_name_from_local_settings()
    )

    session = connect_to_db()
    freelancer: FreelancerModel = get_freelancer_by_name(name=cv_candiate)
    if not freelancer:
        st.error("Kein CV hinterlegt")
        st.stop()
    freelancer_id = freelancer.id
    cv = session.query(CVModel).filter_by(freelancer_id=freelancer_id).first()

    if cv:
        structured_data = cv.structured_data
        # Zeige Formulare zur Bearbeitung an, z.B. JSON-Editor oder spezifische Felder
        st.text_area("Strukturierte CV-Daten", value=structured_data, height=300)

        # Erlaubt Änderungen und Speichern
        if st.button("Speichern"):
            # Aktualisiere die Daten in der DB
            cv.structured_data = st.session_state["neue_daten"]  # Beispiel
            session.commit()
            st.success("CV-Daten aktualisiert!")
    else:
        st.info("Kein CV gefunden. Bitte lade zuerst deinen Lebenslauf hoch.")

    session.close()
