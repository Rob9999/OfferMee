# offermee/dashboard/pages/manual_input.py

import streamlit as st
from jsonschema import ValidationError

# Deine Projektspezifischen Importe
from offermee.dashboard.web_dashboard import stop_if_not_logged_in, log_info, log_error
from offermee.AI.project_processor import ProjectProcessor
from offermee.database.facades.main_facades import ProjectFacade
from offermee.schemas.json.schema_loader import get_schema, validate_json
from offermee.schemas.json.schema_keys import SchemaKey
from offermee.database.db_connection import session_scope
from offermee.database.transformers.project_model_transformer import json_to_db
from offermee.dashboard.transformers.to_sreamlit import (
    create_streamlit_form_from_json_schema,
)


def render():
    """
    Streamlit page: multi-step input & validation flow.

    1) Large Raw-Text field for the job/project description (with hint: Ctrl+Enter).
    2) "Analyze with AI" => fill session_state["project_form_data"].
    3) Show validation form => user can see/edit fields (including enum -> selectbox).
    4) "Validate Data" => check JSON schema => if OK, "manual_input_valid" = True.
    5) "Save to DB" => only visible if valid.
    """
    st.header("Manual Project Input (Multi-Step)")
    stop_if_not_logged_in()

    # --- Load your project schema
    schema = get_schema(SchemaKey.PROJECT)

    # --- Initialize session state
    if "raw_input_text" not in st.session_state:
        st.session_state["raw_input_text"] = ""
    if "analysis_done" not in st.session_state:
        st.session_state["analysis_done"] = False
    if "manual_input_valid" not in st.session_state:
        st.session_state["manual_input_valid"] = False
    if "project_form_data" not in st.session_state:
        st.session_state["project_form_data"] = {}

    def invalidate_analysis():
        """When raw text changes, drop the old AI result + validation status."""
        st.session_state["analysis_done"] = False
        st.session_state["project_form_data"] = {}
        st.session_state["manual_input_valid"] = False

    def invalidate_validation():
        """When user modifies form fields, reset the validation flag."""
        st.session_state["manual_input_valid"] = False

    # --- Step 1: Big raw text input
    st.write("### 1) Raw Project Description")
    new_raw_text = st.text_area(
        label=(
            "Paste the job description (if any):\n"
            "(Hinweis: Drücke Strg+Enter bzw. Cmd+Enter, um den Text zu übernehmen.)"
        ),
        value=st.session_state["raw_input_text"],
        height=200,
    )

    # Kleiner Hinweis (optional) - Du kannst auch st.caption(...) machen:
    # st.caption("Drücke Strg+Enter (Windows) oder Cmd+Enter (Mac), um den Text zu übernehmen.")

    # If user modifies raw text => AI analysis invalid
    if new_raw_text != st.session_state["raw_input_text"]:
        st.session_state["raw_input_text"] = new_raw_text
        invalidate_analysis()

    # --- Step 2: "Analyze with AI" button
    if (
        st.session_state["raw_input_text"].strip()
        and not st.session_state["analysis_done"]
    ):
        if st.button("Analyze Raw Input (AI)"):
            try:
                processor = ProjectProcessor()
                result = processor.analyze_project(st.session_state["raw_input_text"])
                if not result or "project" not in result:
                    st.error("AI analysis did not return a valid 'project' structure.")
                else:
                    st.session_state["project_form_data"] = result["project"]
                    st.session_state["analysis_done"] = True
                    st.session_state["manual_input_valid"] = False
                    st.success("AI analysis complete. Please review the fields below.")
            except Exception as e:
                log_error(__name__, f"Error during AI analysis: {e}")
                st.error(f"Error during AI analysis: {e}")

    # --- Step 3: Validation form
    if st.session_state["analysis_done"]:
        updated_data = create_streamlit_form_from_json_schema(
            schema, st.session_state["project_form_data"]
        )

        # If user modifies anything in the form => we must re-validate
        if updated_data != st.session_state["project_form_data"]:
            st.session_state["project_form_data"] = updated_data
            invalidate_validation()

        # --- Step 4: Validate Data
        if st.button("Validate Data"):
            try:
                data_to_validate = {"project": st.session_state["project_form_data"]}
                validate_json(data_to_validate, schema)
                st.session_state["manual_input_valid"] = True
                st.success("Data is valid according to the schema. You can now save.")
            except ValidationError as ve:
                st.session_state["manual_input_valid"] = False
                st.error(f"Validation Error: {ve.message}")
            except Exception as e:
                st.session_state["manual_input_valid"] = False
                st.error(f"Unexpected error during validation: {e}")

        # --- Step 5: Save to DB (only if valid)
        if st.session_state["manual_input_valid"]:
            if st.button("Save to DB"):
                try:
                    final_data = {"project": st.session_state["project_form_data"]}
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
                    new_project = json_to_db(final_data)
                    st.success(f"Project '{new_project.title}' saved to DB.")
                except Exception as e:
                    log_error(__name__, f"Error saving to DB: {e}")
                    st.error(f"Error while saving: {e}")
