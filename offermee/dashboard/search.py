from typing import Any, Dict, List
import streamlit as st

from offermee.dashboard.widgets.to_sreamlit import (
    create_search_widget_from_json_schema,
    display_dict_as_widgets,
)
from offermee.dashboard.helpers.web_dashboard import stop_if_not_logged_in
from offermee.database.facades.main_facades import ProjectFacade
from offermee.database.models.main_models import ProjectModel
from offermee.database.transformers.to_json_schema import db_model_to_json_schema


def render():
    st.header("Projekte suchen")
    stop_if_not_logged_in()

    project_json_schema = db_model_to_json_schema(ProjectModel)

    project_search_fields = create_search_widget_from_json_schema(project_json_schema)

    if project_search_fields:
        st.success("Suche abgeschlossen! Ergebnisse anzeigen...")
        projects: List[Dict[str, Any]] = ProjectFacade.get_all_by(project_search_fields)
        st.success(f"Found {len(projects)} projects:")
        display_dict_as_widgets(projects)
