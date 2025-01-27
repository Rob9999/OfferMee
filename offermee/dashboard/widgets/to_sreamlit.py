import json
from typing import Any, Callable, Dict, List, Optional
import streamlit as st

from offermee.utils.international import _T
from offermee.dashboard.helpers.web_dashboard import log_debug, log_info
from offermee.schemas.json.schema_loader import validate_json
from offermee.utils.container import Container


def create_streamlit_edit_form_from_json_schema(
    container: Container,
    container_data_path: str = "data",
    container_schema_path: str = "schema",
    container_control_path: str = "control",
    label: str = "Your Form",
) -> bool:
    """
    Dynamically generates Streamlit input fields based on a JSON schema and returns user input data.

    - Handles common JSON schema types: string, number, integer, array, boolean, object.
    - Supports enums, min/max validation, and nested objects.
    - Assumes `data` provides default values for the fields.

    Args:
        schema (dict): JSON schema to create input fields from.
        outer_form_level (bool): Signals the out form level, that gets a submit button

    container:
        in (dict):  st.session_state[container_label]: The data to view and edit.
        out (dict): st.session_state[container_label]: The currently edited data.

    Returns:
        True if Ok button is pressed; Otherwise False
    """

    def validate_json_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validates JSON schema and JSON data against a JSON schema to ensure it is compatible with the Streamlit form generator.

        Args:
            data (Dict[str, Any]): The JSON data to validate.
            schema (Dict[str, Any]): The JSON schema to validate against.

        Returns:
            bool: True if the data is valid, False otherwise.
        """
        log_info(__name__, "Validate JSON data ...")
        validate_json(json_data=json.dumps(data), schema=schema)
        log_info(__name__, "Validate JSON data done.")
        return True

    def clamp_value(
        value,
        min_value=None,
        max_value=None,
    ):
        if min_value is not None:
            value = max(value, min_value)
        if max_value is not None:
            value = min(value, max_value)
        return value

    def set_changed(container: Container = container) -> bool:
        """User has changed the data."""
        container.set_value(
            container_control_path,
            {
                "changed": True,
            },
        )
        # if changed unset wantstore, because the user needs to admit explicitly saving the changes
        set_wantstore(container=container, wantstore=False)
        log_info(__name__, f"set_changed(True): {container_control_path}")
        return True

    def set_wantstore(container: Container = container, wantstore: bool = True) -> bool:
        """User admits explicitly to save changes."""
        container.set_value(
            container_control_path,
            {
                "wantstore": wantstore,
            },
        )
        log_info(__name__, f"set_wantstore({wantstore}): {container_control_path}")
        return True

    def save_all_values(
        container: Container = container,
        path_name: str = container_data_path,
        control_path: str = container_control_path,
    ) -> bool:
        try:
            if not container:
                raise ValueError("Container is None.")
            log_info(
                __name__,
                f"Saving all values of '{path_name}' into container '{container.get_name()}' ...",
            )
            for key in st.session_state.keys():
                if key.startswith(path_name):
                    container.set_value(key, st.session_state.get(key))
                    # log_debug(
                    #    __name__, f"set_value('{key}',{st.session_state.get(key)})"
                    # )
                elif key.startswith(control_path):
                    container.set_value(key, st.session_state.get(key))
                    log_debug(
                        __name__, f"set_value('{key}',{st.session_state.get(key)})"
                    )
                else:
                    # log_debug(
                    #    __name__,
                    #    f"on_click --> st.session_state.get('{key}'): {st.session_state.get(key)}",
                    # )
                    pass
            log_info(
                __name__,
                f"Saved all values of '{path_name}' into container '{container.get_name()}'.",
            )
            # validate_json_data(
            #    container.get_value(path_name),
            #    container.get_value(container_schema_path),
            # )
            return True
        except Exception as e:
            log_info(__name__, f"Error while saving values of '{path_name}': {e}")
            return False

    def create_callable(
        container: Container = None,
        path_name: str = None,
        control_path: str = None,
    ) -> Callable[[], None]:
        """
        Returns a callable function that, when invoked, sets container value according to the path in to the container.
        """

        def on_click():
            save_all_values(
                container=container, path_name=path_name, control_path=control_path
            )

        return on_click

    def render_field(
        current_edited_data_path: str,
        field_name: str,
        field_def: Dict[str, Any],
        current_value: Any,
    ):
        def default_value_for(item_schema):
            # Erzeugen Sie basierend auf dem Typ im Schema einen sinnvollen Standardwert
            t = item_schema.get("type")
            if t == "string":
                return ""
            elif t == "number":
                return 0.0
            elif t == "integer":
                return 0
            elif t == "boolean":
                return False
            elif t == "object":
                return {}
            elif t == "array":
                return []
            return None

        field_type = field_def.get("type")
        if isinstance(field_type, list):
            field_type = field_type[
                0
            ]  # Handle multi-type fields by taking the first type.

        description = field_def.get("description", "")
        enum_values = field_def.get("enum")
        minimum = field_def.get("minimum")
        maximum = field_def.get("maximum")
        if field_name.startswith("["):
            current_edited_data_path += f"{field_name}"
            label_name = field_name[1:-1]  # remove brackets
        else:
            current_edited_data_path += "." + f"{field_name}"
            label_name = field_name

        # Handle enums
        if enum_values:
            if current_value not in enum_values:
                current_value = enum_values[0]
            return st.selectbox(
                label=label_name,
                key=current_edited_data_path,
                options=enum_values,
                index=enum_values.index(current_value),
                help=description,
            )

        # Handle different field types
        if field_type == "string":
            return st.text_input(
                label=label_name,
                value=current_value or "",
                key=current_edited_data_path,
                help=description,
            )

        elif field_type == "number":
            current_value = float(current_value) if current_value is not None else 0.0
            current_value = clamp_value(current_value, minimum, maximum)
            return st.number_input(
                label=label_name,
                key=current_edited_data_path,
                value=current_value,
                min_value=minimum,
                max_value=maximum,
                help=description,
            )

        elif field_type == "integer":
            current_value = int(current_value) if current_value is not None else 0
            current_value = clamp_value(current_value, minimum, maximum)
            return st.number_input(
                label=label_name,
                key=current_edited_data_path,
                value=current_value,
                min_value=minimum,
                max_value=maximum,
                step=1,
                help=description,
            )

        elif field_type == "boolean":
            return st.checkbox(
                label=label_name,
                key=current_edited_data_path,
                value=bool(current_value),
                help=description,
            )

        elif field_type == "array":
            if not isinstance(current_value, list):
                current_value = []
            items_def = field_def.get("items")

            with st.container(key=current_edited_data_path, border=True):
                st.write(f"### {label_name}")

                updated_list = []
                index = 0
                if len(current_value) == 0:
                    # show button to insert first entry
                    if st.button(
                        "➕", key=f"add_first_{index}_{current_edited_data_path}"
                    ):
                        save_all_values()
                        set_changed()
                        # insert an array
                        container.set_value(
                            path_name=current_edited_data_path, value=[]
                        )
                        # insert array's first entry, a default value
                        container.insert(
                            path_name=current_edited_data_path,
                            index=index,
                            value=default_value_for(items_def),
                        )
                        # return current_value
                        st.rerun(scope="app")
                else:
                    while index < len(current_value):
                        current_val = current_value[index]

                        # Layout mit Buttons und Feld
                        col1, col2, col3, col4 = st.columns([1, 20, 1, 1])
                        with col1:
                            # Button zum Einfügen eines neuen Elements oben
                            if st.button(
                                "➕↑",
                                key=f"add_up_{index}_entry_in_{current_edited_data_path}",
                            ):
                                # Füge ein neues Standard-Element vor dem aktuellen hinzu
                                save_all_values()
                                set_changed()
                                container.insert(
                                    path_name=current_edited_data_path,
                                    index=index,
                                    value=default_value_for(items_def),
                                )
                                # return current_value
                                st.rerun()

                        with col2:
                            # Render des aktuellen Listeneintrags
                            if isinstance(current_val, dict):
                                rendered_value = nestable(
                                    current_edited_data_path=f"{current_edited_data_path}[{index}]",
                                    schema=items_def,
                                    data=current_val,
                                )
                            else:
                                rendered_value = render_field(
                                    current_edited_data_path=current_edited_data_path,
                                    field_name=f"[{index}]",
                                    field_def=items_def,
                                    current_value=current_val,
                                )
                            updated_list.append(rendered_value)

                        with col3:
                            # Button zum Einfügen eines neuen Elements unten
                            if st.button(
                                "➕↓",
                                key=f"add_down_{index}_entry_in_{current_edited_data_path}",
                            ):
                                save_all_values()
                                set_changed()
                                container.insert(
                                    path_name=current_edited_data_path,
                                    index=index + 1,
                                    value=default_value_for(items_def),
                                )
                                # return current_value
                                st.rerun()

                        with col4:
                            # Button zum Entfernen des aktuellen Elements
                            if st.button(
                                "➖",
                                key=f"remove_{index}_entry_of_{current_edited_data_path}",
                            ):
                                save_all_values()
                                set_changed()
                                container.pop(
                                    path_name=current_edited_data_path, index=index
                                )
                                # return current_value
                                st.rerun()

                        index += 1

                    # Nach der Iteration die aktualisierte Liste zurückgeben
                    return updated_list

        elif field_type == "object":
            with st.container(key=current_edited_data_path, border=True):
                # st.write(
                #    f"### {field_name}",
                #
                # )
                return nestable(
                    current_edited_data_path=current_edited_data_path,
                    schema=field_def,
                    data=current_value,
                )

        else:
            # Fallback for unknown types
            return st.text_input(
                label=f"{label_name} (unhandled type: {field_type})",
                key=current_edited_data_path,
                value=str(current_value or ""),
                help=description,
            )

    def nestable(
        current_edited_data_path: str,
        schema: Dict[str, Any],
        data: Dict[str, Any] = None,
    ):
        # Initialize data if None
        if data is None:
            data = {}
        # Add title from schema if available
        if "title" in schema:
            st.title(schema["title"])

        user_data = {}
        properties = schema.get("properties", {})

        for field_name, field_def in properties.items():
            current_value = data.get(field_name, field_def.get("default"))
            user_data[field_name] = render_field(
                current_edited_data_path=current_edited_data_path,
                field_name=field_name,
                field_def=field_def,
                current_value=current_value,
            )

        return user_data

    log_info(__name__, f"Show edit form of '{label}'")
    st.markdown(f"**{label}**")
    schema = container.get_value(container_schema_path)
    data = container.get_value(container_data_path)
    if schema is None:
        raise ValueError(
            f"Schema  is None: container '{container.get_name()}' path '{container_schema_path}'."
        )
    if data is None:
        raise ValueError(
            f"Data is None: container '{container.get_name()}' path '{container_data_path}'."
        )
    # validate_json_data(data, schema)
    nestable(current_edited_data_path=container_data_path, schema=schema, data=data)
    if st.button(
        _T("OK"),
        icon=":material/thumb_up:",
        key=f"{container_control_path}.wantstore",
        on_click=create_callable(
            container=container,
            path_name=container_data_path,
            control_path=container_control_path,
        ),
    ):
        log_info(__name__, f"Editing data of '{container_data_path}' is done.")
        return True
    return False


def create_search_widget_from_json_schema(
    schema: Dict[str, Any], prefix: str = ""
) -> Dict[str, Any]:
    """
    Generates a Streamlit search form with filters based on a JSON schema.

    Args:
        schema (Dict[str, Any]): JSON schema defining the search fields.
        prefix (str): Prefix for nested field names to handle hierarchy.

    Returns:
        Dict[str, Any]: A dictionary of user input values for the search filters.
    """
    st.write("### Search Filters")
    user_inputs = {}

    properties = schema.get("properties", {})

    for field_name, field_def in properties.items():
        field_key = f"{prefix}.{field_name}" if prefix else field_name
        field_type = field_def.get("type")
        description = field_def.get("description", "")
        enum_values = field_def.get("enum")

        if field_type == "string":
            if enum_values:
                user_inputs[field_key] = st.selectbox(
                    label=f"{field_key}",
                    options=enum_values,
                    help=description,
                )
            else:
                user_inputs[field_key] = st.text_input(
                    label=f"{field_key}",
                    help=description,
                )

        elif field_type == "number":
            user_inputs[field_key] = st.number_input(
                label=f"{field_key}",
                help=description,
            )

        elif field_type == "integer":
            user_inputs[field_key] = st.number_input(
                label=f"{field_key}",
                step=1,
                format="%d",
                help=description,
            )

        elif field_type == "boolean":
            user_inputs[field_key] = st.checkbox(
                label=f"{field_key}",
                help=description,
            )

        elif field_type == "array":
            array_items = []
            index = 0
            st.write(f"### {field_key} (array items)")
            while True:
                item_key = f"{field_key}[{index}]"
                new_item = st.text_input(
                    label=f"{item_key}",
                    key=item_key,
                    help=description,
                )
                if new_item:
                    array_items.append(new_item)
                add_button = st.button(
                    f"Add item to {field_key}", key=f"add_{field_key}_{index}"
                )
                if add_button:
                    index += 1
                    continue
                else:
                    break
            user_inputs[field_key] = array_items

        elif field_type == "object":
            nested_inputs = create_search_widget_from_json_schema(
                field_def, prefix=field_key
            )
            user_inputs.update(nested_inputs)

        else:
            st.write(f"{field_key} (unhandled type: {field_type})")

    if st.button("Search"):
        st.write("Search results would be processed based on:")
        st.json(user_inputs)

    return user_inputs


def display_dict_as_widgets(data: Dict[str, Any], prefix: str = "") -> None:
    """
    Dynamically generates Streamlit widgets to display and interact with data from a dictionary.

    Args:
        data (Dict[str, Any]): The dictionary containing the data to display.
        prefix (str): A prefix for nested keys to maintain hierarchy.

    Returns:
        None
    """
    for key, value in data.items():
        display_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            st.write(f"### {display_key} (Nested Object)")
            display_dict_as_widgets(value, prefix=display_key)

        elif isinstance(value, list):
            st.write(f"### {display_key} (Array)")
            for i, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    st.write(f"#### {display_key}[{i}]")
                    display_dict_as_widgets(item, prefix=f"{display_key}[{i}]")
                else:
                    st.text_input(
                        label=f"{display_key}[{i}]",
                        value=str(item),
                        key=f"{display_key}[{i}]",
                    )

        elif isinstance(value, (int, float)):
            st.number_input(
                label=display_key,
                value=value,
                key=display_key,
            )

        elif isinstance(value, bool):
            st.checkbox(
                label=display_key,
                value=value,
                key=display_key,
            )

        elif isinstance(value, str):
            st.text_input(
                label=display_key,
                value=value,
                key=display_key,
            )

        else:
            st.write(f"{display_key}: (Unsupported Type: {type(value).__name__})")
