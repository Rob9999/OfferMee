from typing import Any, Dict, List
import streamlit as st
from offermee.dashboard.helpers.web_dashboard import stop_if_not_logged_in
from offermee.database.facades.main_facades import FreelancerFacade


def templates_render():
    st.header("Standardangebotstemplate")
    stop_if_not_logged_in()

    try:
        # Get all Freelancers
        freelancers: List[Dict[str, Any]] = FreelancerFacade.get_all()

        if not freelancers:
            st.info("Keine Freelancer in der Datenbank gefunden.")
            return

        # Make a table of all Freelancers
        freelancer_table_data = []
        for freelancer in freelancers:
            # Append the desired view infos
            freelancer_table_data.append(
                {
                    "ID": freelancer.get("id"),
                    "Name": freelancer.get("name"),
                }
            )

        # View the table
        st.subheader("Verfügbare Lebensläufe")
        selected_freelancer_id = st.selectbox(
            "Wählen Sie einen Freelancer aus:",
            options=[cv["ID"] for cv in freelancer_table_data],
            format_func=lambda x: f"#{x},{next(item['Name'] for item in freelancer_table_data if item['CV-ID'] == x)}",
        )

        # Template language selection (optional) # TODO
        language = st.selectbox(
            "Sprache des Templates:", options=["de", "en", "fr", "es"]
        )
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
                FreelancerFacade.update(
                    selected_freelancer_id, {"offer_template": current_template}
                )
                st.success("Template erfolgreich gespeichert!")
            else:
                st.error(
                    "Freelancer-Profil nicht gefunden. Bitte hinterlegen Sie Ihren CV."
                )
    except Exception as e:
        st.error(f"Fehler beim Speichern des Templates: {e}")
