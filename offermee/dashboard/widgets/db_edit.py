import traceback
from typing import Any, Dict, List, Optional
import streamlit as st
from offermee.database.transformers.to_json_schema import (
    build_full_json_schema,
    db_model_to_json_schema,
)
from offermee.utils.international import _T
from offermee.dashboard.widgets.to_sreamlit import (
    create_streamlit_edit_form_from_json_schema,
)
from offermee.dashboard.helpers.web_dashboard import (
    log_error,
    log_info,
    join_container_path,
)
from offermee.database.facades.main_facades import (
    BaseFacade,
    FreelancerFacade,
)
from offermee.utils.container import Container

MODEL_NAME_TO_FACADE_MAPPING = {"freelancer": FreelancerFacade}


def get_facade(model_name: str) -> Optional[BaseFacade]:
    return MODEL_NAME_TO_FACADE_MAPPING.get(model_name.lower())


def get_table_data(data: Dict[str, Any], length: int, exclude_keys: List[str] = None):
    if not data:
        ValueError("Missing data")
    if not length:
        ValueError("Missing length")
    # make a string of the data of the dictionary, optional exclude keys
    string = ""
    for key, content in data.items():
        if exclude_keys and key in exclude_keys:
            continue
        content_string = str(content)
        if length < 0:
            string += ", " + content_string
            continue
        current_length = len(string)
        if current_length + 2 >= length - 3:
            # append ellipses and go out
            string += "..."
            return string
        string += ", " + content_string[: (length - current_length - 2)]
    return string


def record_selection_form(
    label: str, data: List[Dict[str, Any]], container: Container, result_path: str
):
    # log_info
    with st.form(key=f"form_select_record_{label}"):
        st.subheader(f"{label}")
        if not data:
            st.info(_T("No data found in the database. Please insert data first."))
            st.stop()

        # Build a list of data for display
        table_data = []
        for record in data:
            table_data.append(
                {
                    "ID": record.get("id"),
                    "RECORD": get_table_data(
                        data=record, length=50, exclude_keys=["id"]
                    ),
                }
            )

        # Prepare options and set default selection
        options = {record["ID"]: record for record in table_data}
        options_keys = list(options.keys())

        st.markdown(f"**{_T('Available')}**")
        try:
            selected_record_id = st.selectbox(
                _T("Select One:"),
                options=options_keys,
                index=0 if len(options_keys) > 0 else None,
                format_func=lambda x: f"#{x}, {options[x]['RECORD']}",
            )
        except KeyError as k:
            raise KeyError(f"KeyError while selecting record: {k}")
        except Exception as e:
            log_error("Error during record selection process: {}", str(e))
            raise e

        if st.form_submit_button(
            _T("OK"),
            icon=":material/thumb_up:",
        ):
            log_info(__name__, f"Selecting record #{selected_record_id} ...")
            container.set_value(
                result_path,
                next(
                    (
                        record
                        for record in data
                        if record.get("id") == selected_record_id
                    ),
                    None,
                ),
            )
            log_info(__name__, f"Selected record #{selected_record_id}.")


def edit(
    label: str, page_root: str, container: Container, model_name: str, operator: str
):
    """
    1. Let the user select the record
    2. Load the complete record flat
    3. Offer the user to load all related data.
    3.1 If the user selects full load of record (including related data) then load all related data
    4. The user then may change the loaded data and if the user pressed the SAVE Button save all data including related data

    Args:
        label (str): _description_
        page_root (str): _description_
        container (Container): _description_
        model_name (str): _description_
        operator (str): _description_
    """
    try:
        # 1. let the user select the record
        # 2. load the complete record flat
        edit_path = join_container_path(page_root, "edit")
        control_path = join_container_path(edit_path, "control")
        record_path = join_container_path(edit_path, "record")
        facade: BaseFacade = get_facade(model_name=model_name)
        if not facade:
            raise ValueError(f"Unknown model_name='{model_name}'")
        flat_records = facade.get_all()
        record_selection_form(
            label=label,
            data=flat_records,
            container=container,
            result_path=record_path,
        )

        # 3. Offer the user to load all related data.
        schema_path = join_container_path(edit_path, "schema")
        load_mode_path = join_container_path(control_path, "load_mode")
        sentinel = {}
        record: Dict[str, Any] = container.get_value(record_path, sentinel)
        if record == sentinel:
            return
        if container.get_value(schema_path, sentinel) == sentinel:
            container.set_value(
                schema_path, db_model_to_json_schema(facade.SERVICE.MODEL)
            )

        @st.dialog(_T("Dismiss unsaved data?"))
        def change_data_load_mode():
            # make a hint
            st.write(
                _T(
                    "Change data load mode would dismiss all unsaved data.\nDo you want to save your data changes first?"
                )
            )
            col1, col2 = st.columns([1, 1])
            dismiss_data = col1.button(_T("No, Dismiss Data"))
            if col2.button(_T("Cancel")):
                st.rerun()
            if dismiss_data:
                # get current value
                load_mode_value = container.get_value(load_mode_path, "flat")
                if load_mode_value == "flat":
                    # Toggle to full
                    # 3.1 If the user selects full load of record (including related data) then load all related data
                    record_full = facade.get_by_id_with_relations(
                        record_id=record.get("id")
                    )
                    if not record_full:
                        raise ValueError("Missing full record")
                    container.set_value(record_path, record_full)
                    container.set_value(
                        schema_path, build_full_json_schema(facade.SERVICE.MODEL)
                    )
                    container.set_value(load_mode_path, "full")
                else:
                    # Toggle to flat
                    record_flat = facade.get_by_id(record_id=record.get("id"))
                    if not record_flat:
                        raise ValueError("Missing flat record")
                    container.set_value(record_path, record_flat)
                    container.set_value(
                        schema_path, db_model_to_json_schema(facade.SERVICE.MODEL)
                    )
                    container.set_value(load_mode_path, "flat")
                st.rerun()

        load_selection_map = {"full": _T("Full"), "flat": _T("Flat")}
        load_options = load_selection_map.values()
        st.radio(
            label=_T("Select Data Load Mode"),
            key="select_data_load_mode",
            options=load_options,
            index=1 if container.get_value(load_mode_path, "flat") == "flat" else 0,
            on_change=change_data_load_mode,
        )

        # log_debug(__name__, f"4. data: {container.get_value(record_path)}")
        # 4. The user then may change the loaded data and if the user pressed the SAVE Button save all data including related data
        create_streamlit_edit_form_from_json_schema(
            container=container,
            container_data_path=record_path,
            container_schema_path=schema_path,
            container_control_path=control_path,
            label=label,
        )
        edited_record: Dict[str, Any] = container.get_value(record_path)
        wants_to_store_path = join_container_path(control_path, "wantstore")
        wants_to_store = container.get_value(wants_to_store_path, False)

        if edited_record and wants_to_store:
            log_info(__name__, "Could save edited record data ...")
            # container.dump(path=Config.get_instance().get_user_temp_dir())
            # Ask to store changes
            if st.button(_T("Save")):
                log_info(__name__, "Updating record data ...")
                facade.update(
                    record_id=edited_record.get("id"),
                    data=edited_record,
                    updated_by=operator,
                )
                st.success(_T("Record Data Upadated!"))
                log_info(__name__, "Record Data Updated!")
                if st.button(_T("Clear Page")):
                    log_info(__name__, "Clear Page")
                    container.set_value(page_root, None)
                log_info(__name__, "Rerun ...")
                st.rerun()
    except ValueError as ve:
        log_error(__name__, f"ERROR (Value Error) while '{label}': {ve}")
        st.error(f"{_T('Value Error')}:\n{ve}")
    except KeyError as ke:
        log_error(__name__, f"ERROR (Key Error) while '{label}': {ke}")
        st.error(f"{_T('Key Error')}:\n{ke}")
    except TypeError as te:
        log_error(__name__, f"ERROR (Type Error) while '{label}': {te}")
        st.error(f"{_T('Type Error')}:\n{te}")
    except Exception as e:
        log_error(__name__, f"ERROR while '{label}': {e}")
        st.error(f"{_T('Error')}:\n{e}")
        traceback.print_exception(type(e), e, e.__traceback__)
