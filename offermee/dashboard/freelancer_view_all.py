# offermee/dashboard/pages/manual_input.py

import traceback
import streamlit as st
import pandas as pd

# Deine Projektspezifischen Importe
from offermee.config import Config
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    log_error,
    log_info,
    stop_if_not_logged_in,
)
from offermee.database.facades.main_facades import FreelancerFacade
from offermee.utils.international import _T
from offermee.utils.container import Container


def get_title() -> str:
    return _T("View All")


def freelancer_view_all_render():

    st.header("View All Freelancers)")
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    try:
        freelancers = FreelancerFacade.get_all()
        log_info(__name__, f"Fetched {len(freelancers)} Freelancers:\n{freelancers}")
        if freelancers:
            # Definiere die Spalten, die du anzeigen möchtest
            spalten = [
                _T("ID"),
                _T("Name"),
                _T("Role"),
                _T("Availability"),
                _T("Location"),
                _T("Desired Rate Min"),
                _T("Desired Rate Max"),
                _T("Status"),
                _T("Email"),
                _T("Website"),
                _T("Soft Skills"),
                _T("Tech Skills"),
                _T("Preferred Language"),
                _T("Preferred Currency"),
                _T("Created At"),
                _T("Updated At"),
                _T("Offer Template"),
            ]

            # Sammle die Daten in einer Liste von Dictionaries
            daten = []
            for freelancer in freelancers:
                daten.append(
                    {
                        _T("ID"): freelancer.get("id"),
                        _T("Name"): freelancer.get("name"),
                        _T("Role"): freelancer.get("role"),
                        _T("Availability"): freelancer.get("availability"),
                        _T("Location"): freelancer.get("location"),
                        _T("Desired Rate Min"): freelancer.get("desired_rate_min"),
                        _T("Desired Rate Max"): freelancer.get("desired_rate_max"),
                        _T("Status"): freelancer.get("status"),
                        _T("Email"): freelancer.get("email"),
                        _T("Website"): freelancer.get("website"),
                        _T("Preferred Language"): freelancer.get("preferred_language"),
                        _T("Preferred Currency"): freelancer.get("preferred_currency"),
                        _T("Soft Skills"): freelancer.get("soft_skills"),
                        _T("Tech Skills"): freelancer.get("tech_skills"),
                        _T("Created At"): freelancer.get("created_at"),
                        _T("Updated At"): freelancer.get("updated_at"),
                        _T("Offer Template"): freelancer.get("offer_template"),
                    }
                )

            # Erstelle einen DataFrame
            df = pd.DataFrame(daten, columns=spalten)

            # Zeige die Tabelle an
            st.dataframe(df, use_container_width=True)
            # Alternativ kannst du auch st.table verwenden:
            # st.table(df)
        else:
            st.info(_T("No Freelancers found."))
    except Exception as e:
        log_error(__name__, f"Error retrieving Freelancers: {e}")
        st.error(f"{_T('Error retrieving Freelancers')}: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
