# offermee/dashboard/pages/manual_input.py

import traceback
import streamlit as st
import pandas as pd

# Deine Projektspezifischen Importe
from offermee.utils.config import Config
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    log_error,
    log_info,
    stop_if_not_logged_in,
)
from offermee.database.facades.main_facades import CVFacade
from offermee.utils.international import _T
from offermee.utils.container import Container


def get_title() -> str:
    return _T("View All")


def cv_view_all_render():

    st.header(_T("View All CVs"))
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    try:
        cvs = CVFacade.get_all()
        log_info(__name__, f"Fetched {len(cvs)} CVs:\n{cvs}")
        if cvs:
            # Definiere die Spalten, die du anzeigen möchtest
            spalten = [
                _T("ID"),
                _T("Name"),
                _T("Summary"),
                _T("Raw Text"),
                _T("Created At"),
                _T("Updated At"),
                _T("Structured Data"),
            ]

            # Sammle die Daten in einer Liste von Dictionaries
            daten = []
            for cv in cvs:
                daten.append(
                    {
                        _T("ID"): cv.get("id"),
                        _T("Name"): cv.get("name"),
                        _T("Summary"): cv.get("summary"),
                        _T("Raw Text"): cv.get("cv_raw_text"),
                        _T("Created At"): cv.get("created_at"),
                        _T("Updated At"): cv.get("updated_at"),
                        _T("Structured Data"): cv.get("cv_structured_data"),
                    }
                )

            # Erstelle einen DataFrame
            df = pd.DataFrame(daten, columns=spalten)

            # Zeige die Tabelle an
            st.dataframe(df, use_container_width=True)
            # Alternativ kannst du auch st.table verwenden:
            # st.table(df)
        else:
            st.info(_T("No CVs found."))
    except Exception as e:
        log_error(__name__, f"Error retrieving CVs: {e}")
        st.error(f"{_T('Error retrieving CVs')}: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
