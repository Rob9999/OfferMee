import streamlit as st
from offermee.dashboard.web_dashboard import stop_if_not_logged_in
from offermee.database.db_connection import connect_to_db
from offermee.database.models.freelancer_model import FreelancerModel


def render():
    st.header("Standardangebotstemplate")
    stop_if_not_logged_in()

    session = connect_to_db()

    try:
        # Laden des aktuellen Templates
        freelancer = session.query(FreelancerModel).first()
        current_template = (
            freelancer.offer_template
            if freelancer and freelancer.offer_template
            else ""
        )

        template = st.text_area(
            "Geben Sie Ihr Angebotstemplate ein:", value=current_template, height=300
        )

        if st.button("Speichern"):
            if freelancer:
                freelancer.offer_template = template
                session.commit()
                st.success("Template erfolgreich gespeichert!")
            else:
                st.error(
                    "Freelancer-Profil nicht gefunden. Bitte hinterlegen Sie Ihren CV."
                )
    except Exception as e:
        st.error(f"Fehler beim Speichern des Templates: {e}")
    finally:
        session.close()
