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
from offermee.database.facades.main_facades import ProjectFacade
from offermee.utils.international import _T
from offermee.utils.container import Container


def rfp_view_all_render():

    st.header("View Requests For Proposal (RFPs)")
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    try:
        rfps = ProjectFacade.get_all()
        log_info(__name__, f"Fetched {len(rfps)} RFPs:\n{rfps}")
        if rfps:
            # Definiere die Spalten, die du anzeigen möchtest
            spalten = [
                _T("ID"),
                _T("Title"),
                _T("Description"),
                _T("Location"),
                _T("Must Haves"),
                _T("Nice to Haves"),
                _T("Tasks"),
                _T("Responsibilities"),
                _T("Hourly Rate"),
                _T("Other Conditions"),
                _T("Contact Person"),
                _T("Contact Person Email"),
                _T("Provider"),
                _T("Provider Link"),
                _T("Start Date"),
                _T("End Date"),
                _T("Duration"),
                _T("Extension Option"),
                _T("Original Link"),
                _T("Status"),
                _T("Created At"),
                _T("Updated At"),
            ]

            # Sammle die Daten in einer Liste von Dictionaries
            daten = []
            for rfp in rfps:
                daten.append(
                    {
                        _T("ID"): rfp.get("id"),
                        _T("Title"): rfp.get("title"),
                        _T("Description"): rfp.get("description"),
                        _T("Location"): rfp.get("location"),
                        _T("Must Haves"): rfp.get("must_haves"),
                        _T("Nice to Haves"): rfp.get("nice_to_haves"),
                        _T("Tasks"): rfp.get("tasks"),
                        _T("Responsibilities"): rfp.get("responsibilities"),
                        _T("Hourly Rate"): rfp.get("hourly_rate"),
                        _T("Other Conditions"): rfp.get("other_conditions"),
                        _T("Contact Person"): rfp.get("contact_person"),
                        _T("Contact Person Email"): rfp.get("contact_person_email"),
                        _T("Provider"): rfp.get("provider"),
                        _T("Provider Link"): rfp.get("provider_link"),
                        _T("Start Date"): rfp.get("start_date"),
                        _T("End Date"): rfp.get("end_date"),
                        _T("Duration"): rfp.get("duration"),
                        _T("Extension Option"): rfp.get("extension_option"),
                        _T("Original Link"): rfp.get("original_link"),
                        _T("Status"): rfp.get("status"),
                        _T("Created At"): rfp.get("created_at"),
                        _T("Updated At"): rfp.get("updated_at"),
                    }
                )

            # Erstelle einen DataFrame
            df = pd.DataFrame(daten, columns=spalten)

            # Zeige die Tabelle an
            st.dataframe(df, use_container_width=True)
            # Alternativ kannst du auch st.table verwenden:
            # st.table(df)
        else:
            st.info(_T("No Requests For Proposal found."))
    except Exception as e:
        log_error(__name__, f"Error retrieving offers: {e}")
        st.error(f"{_T('Error retrieving offers')}: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
