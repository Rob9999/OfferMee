from typing import Any, Dict
import streamlit as st

from offermee.dashboard.widgets.uitls import get_valid_next_key


def create_streamlit_edit_form_from_json_schema(
    schema: dict, data: dict = None, outer_form_level: bool = True
) -> tuple[Dict[str, Any], bool]:
    """
    Dynamically generates Streamlit input fields based on a JSON schema and returns user input data.

    - Handles common JSON schema types: string, number, integer, array, boolean, object.
    - Supports enums, min/max validation, and nested objects.
    - Assumes `data` provides default values for the fields.

    Args:
        schema (dict): JSON schema to create input fields from.
        data (dict): Optional default values for the fields.
        outer_form_level (bool): Signals the out form level, that gets a submit button

    Returns:
        dict: User input data.
    """

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

    def render_field(
        field_name,
        field_def,
        current_value,
    ):
        field_type = field_def.get("type")
        if isinstance(field_type, list):
            field_type = field_type[
                0
            ]  # Handle multi-type fields by taking the first type.

        description = field_def.get("description", "")
        enum_values = field_def.get("enum")
        minimum = field_def.get("minimum")
        maximum = field_def.get("maximum")

        # Handle enums
        if enum_values:
            if current_value not in enum_values:
                current_value = enum_values[0]
            return st.selectbox(
                label=f"{field_name}",
                key=get_valid_next_key(),
                options=enum_values,
                index=enum_values.index(current_value),
                help=description,
            )

        # Handle different field types
        if field_type == "string":
            return st.text_input(
                label=f"{field_name}",
                value=current_value or "",
                key=get_valid_next_key(),
                help=description,
            )

        elif field_type == "number":
            current_value = float(current_value) if current_value is not None else 0.0
            current_value = clamp_value(current_value, minimum, maximum)
            return st.number_input(
                label=f"{field_name}",
                key=get_valid_next_key(),
                value=current_value,
                min_value=minimum,
                max_value=maximum,
                help=description,
            )

        elif field_type == "integer":
            current_value = int(current_value) if current_value is not None else 0
            current_value = clamp_value(current_value, minimum, maximum)
            return st.number_input(
                label=f"{field_name}",
                key=get_valid_next_key(),
                value=current_value,
                min_value=minimum,
                max_value=maximum,
                step=1,
                help=description,
            )

        elif field_type == "boolean":
            return st.checkbox(
                label=f"{field_name}",
                key=get_valid_next_key(),
                value=bool(current_value),
                help=description,
            )

        elif field_type == "array":
            if not isinstance(current_value, list):
                current_value = []
            items_def = field_def.get("items")
            with st.container(
                key=f"{field_name}_form_{get_valid_next_key()}", border=True
            ):
                st.write(
                    f"### {field_name}",
                    # key=get_valid_next_key(),
                )
                ret_val = []
                for current_val in current_value:
                    if isinstance(current_val, dict) and "object" in items_def:
                        ret_val.append(nestable(field_def, current_val))
                    else:
                        ret_val.append(
                            render_field(
                                field_name,
                                items_def,
                                current_val,
                            )
                        )
                return ret_val

        elif field_type == "object":
            with st.container(
                key=f"{field_name}_form_{get_valid_next_key()}", border=True
            ):
                # st.write(
                #    f"### {field_name}",
                #    key=get_valid_next_key(),
                # )
                return nestable(field_def, current_value)

        else:
            # Fallback for unknown types
            return st.text_input(
                label=f"{field_name} (unhandled type: {field_type})",
                key=get_valid_next_key(),
                value=str(current_value or ""),
                help=description,
            )

    def nestable(
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
            user_data[field_name] = render_field(field_name, field_def, current_value)

        return user_data

    if outer_form_level:
        with st.form(f"submit_{get_valid_next_key()}"):
            data = nestable(schema=schema, data=data)
            if st.form_submit_button("Submit"):
                st.write("Thanks!")
                return data, True
            return data, False

    else:
        return nestable(schema=schema, data=data), True


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
