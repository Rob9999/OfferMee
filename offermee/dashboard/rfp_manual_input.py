# offermee/dashboard/pages/manual_input.py

from enum import Enum
from typing import Any, Dict, List
import streamlit as st
from jsonschema import ValidationError

# Deine Projektspezifischen Importe
from offermee.config import Config
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    join_container_path,
    stop_if_not_logged_in,
    log_info,
    log_error,
)
from offermee.AI.project_processor import ProjectProcessor
from offermee.database.facades.main_facades import ProjectFacade
from offermee.schemas.json.schema_loader import get_schema, validate_json
from offermee.schemas.json.schema_keys import SchemaKey
from offermee.database.transformers.project_model_transformer import json_to_db
from offermee.dashboard.widgets.to_sreamlit import (
    create_streamlit_edit_form_from_json_schema,
)
from offermee.dashboard.helpers.international import _T
from offermee.utils.container import Container


def rfp_manual_input_render():

    st.header("Manual Request For Proposal (RFP) Input (Multi-Step)")
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    operator = Config.get_instance().get_current_user()

    # --- Initialize
    path_rfps_root = container.make_paths(
        join_container_path(page_root, "rfps"),
        typ=list,
        exists_ok=True,
        force_typ=True,
    )

    class Status(Enum):
        NEW = "new"
        ANALYZED = "analyzed"
        VALIDATED = "validated"
        SAVED = "saved"
        DISCARDED = "discarded"

    rfps: List[Dict[str, Any]] = container.get_value(path_rfps_root, [])
    # rfp = { "raw_text": "...", "schema": { ... }, "data": { ... }, "control": { ... }, "status": Status.NEW }
    # find first rfp that is in status not saved and not discarded (that means has to be worked on)
    rfp_index = next(
        (
            i
            for i, r in enumerate(rfps)
            if r.get("status") in ["new", "analyzed", "validated"]
        ),
        None,
    )
    if rfp_index is None:
        # add new rfp
        rfp_index = len(rfps)
        rfp = {
            "raw_text": "",
            "schema": get_schema(SchemaKey.PROJECT),
            "data": {},
            "control": {"wantstore": False},
            "status": Status.NEW,
        }
        rfps.append(rfp)
        # log_debug(__name__, f"Added new RFP to list:\n{rfp}")
    else:
        rfp = rfps[rfp_index]

    path_rfp_data = path_rfps_root + f"[{rfp_index}].data"
    path_rfp_schema = path_rfps_root + f"[{rfp_index}].schema"
    path_rfp_control = path_rfps_root + f"[{rfp_index}].control"

    def invalidate_analysis(rfp: Dict[str, Any]):
        """When raw text changes, drop the old AI result + validation status."""
        rfp["status"] = "new"
        rfp["data"] = {}
        rfp["control"]["wantstore"] = False

    def invalidate_validation(rfp: Dict[str, Any]):
        """When user modifies form fields, reset the validation flag."""
        rfp["status"] = "analyzed"
        rfp["control"]["wantstore"] = False

    # --- Step 1: Big raw text input
    st.write("### 1) Raw Project Description")
    new_raw_text = st.text_area(
        label=(
            _T(
                "Paste the job description (if any):\n(Note: Press Ctrl+Enter or Cmd+Enter to submit the text.)"
            )
        ),
        value=rfp["raw_text"],
        height=400,
    )

    # Kleiner Hinweis (optional) - Du kannst auch st.caption(...) machen:
    # st.caption("Drücke Strg+Enter (Windows) oder Cmd+Enter (Mac), um den Text zu übernehmen.")

    # If user modifies raw text => AI analysis invalid
    if new_raw_text != rfp["raw_text"]:
        rfp["raw_text"] = new_raw_text
        invalidate_analysis(rfp)

    # --- Step 2: "Analyze with AI" button
    if rfp["raw_text"].strip() and rfp["status"] not in ["analyzed", "validated"]:
        if st.button("Analyze Raw Input (AI)"):
            try:
                processor = ProjectProcessor()
                result = processor.analyze_project(rfp["raw_text"])
                if not result or "project" not in result:
                    st.error("AI analysis did not return a valid 'project' structure.")
                else:
                    rfp["data"] = {"project": result["project"]}
                    rfp["status"] = "analyzed"
                    st.success("AI analysis complete. Please review the fields below.")
            except Exception as e:
                log_error(__name__, f"Error during AI analysis: {e}")
                st.error(f"Error during AI analysis: {e}")

    # --- Step 3: Validation form
    if rfp["status"] in ["analyzed", "validated"]:

        create_streamlit_edit_form_from_json_schema(
            container=container,
            container_data_path=path_rfp_data,
            container_schema_path=path_rfp_schema,
            container_control_path=path_rfp_control,
            label=_T("Project Validate Extracted Data"),
        )
        wants_to_store = container.get_value(
            path_rfps_root + f"[{rfp_index}].control.wantstore", False
        )
        # If user wants to store (data accepted or modified) => we must (re-)validate
        if not wants_to_store:
            invalidate_validation(rfp)

        # --- Step 4: Validate Data
        if st.button("Validate Data"):
            try:
                validate_json(rfp["data"], rfp["schema"])
                rfp["status"] = Status.VALIDATED
                st.success("Data is valid according to the schema. You can now save.")
            except ValidationError as ve:
                rfp["status"] = Status.ANALYZED
                st.error(f"Validation Error: {ve.message}")
            except Exception as e:
                rfp["status"] = Status.ANALYZED
                st.error(f"Unexpected error during validation: {e}")

        # --- Step 5: Save to DB (only if valid)
        if rfp["status"] == Status.VALIDATED:
            if st.button("Save to DB"):
                try:
                    final_data = rfp["data"]
                    original_link = final_data["project"].get("original-link")
                    if original_link:
                        existing = ProjectFacade.get_first_by(
                            {"original_link": original_link}
                        )
                        if existing:
                            st.warning(
                                "A project with that 'original-link' already exists."
                            )
                            return
                    # create and save
                    new_project = json_to_db(final_data).to_dict()
                    ProjectFacade.create(new_project, operator)
                    rfps[rfp_index]["status"] = Status.SAVED
                    st.success(f"Project '{new_project.title}' saved to DB.")
                except Exception as e:
                    log_error(__name__, f"Error saving to DB: {e}")
                    st.error(f"Error while saving: {e}")
