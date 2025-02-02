import json
from typing import Any, Callable, Dict, List, Optional, Union
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
    Generiert dynamisch Streamlit-Eingabefelder basierend auf einem JSON-Schema.
    Die Funktion verarbeitet gängige JSON-Schema-Typen wie string, number, integer,
    array, boolean und object. Dabei werden auch enums, min/max-Validierungen und
    verschachtelte Objekte unterstützt.

    Die Daten werden in einem eigenen Container gehalten, sodass die Applikation
    unabhängig von Streamlit in andere Web-Umgebungen integriert werden kann.

    Args:
        container (Container): Container, der die Daten und das Schema enthält.
        container_data_path (str): Pfad im Container, in dem die Daten liegen.
        container_schema_path (str): Pfad im Container, in dem das Schema liegt.
        container_control_path (str): Pfad im Container, in dem Steuerinformationen gespeichert werden.
        label (str): Überschrift für das Formular.

    Returns:
        bool: True, wenn der OK-Button gedrückt wurde, ansonsten False.
    """

    def validate_json_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validiert JSON-Daten anhand eines JSON-Schemas.

        Args:
            data (Dict[str, Any]): Zu validierende JSON-Daten.
            schema (Dict[str, Any]): Das JSON-Schema.

        Returns:
            bool: True, wenn die Daten valide sind, ansonsten False.
        """
        log_info(__name__, "Validate JSON data ...")
        # Wir gehen davon aus, dass validate_json im Fehlerfall eine Exception wirft
        validate_json(json_data=json.dumps(data), schema=schema)
        log_info(__name__, "Validate JSON data done.")
        return True

    def clamp_value(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ) -> Union[int, float]:
        """
        Begrenzt einen numerischen Wert auf einen minimalen und maximalen Wert.

        Args:
            value (int|float): Der zu begrenzende Wert.
            min_value (int|float, optional): Minimaler erlaubter Wert.
            max_value (int|float, optional): Maximaler erlaubter Wert.

        Returns:
            int|float: Der begrenzte Wert.
        """
        if min_value is not None:
            value = max(value, min_value)
        if max_value is not None:
            value = min(value, max_value)
        return value

    def set_changed() -> bool:
        """Setzt im Container, dass der Nutzer Änderungen vorgenommen hat."""
        container.set_value(
            container_control_path,
            {"changed": True},
        )
        # Bei Änderung wird "wantstore" zurückgesetzt, da der Nutzer explizit das Speichern bestätigen muss.
        set_wantstore(wantstore=False)
        log_info(__name__, f"set_changed(True): {container_control_path}")
        return True

    def set_wantstore(wantstore: bool = True) -> bool:
        """Setzt im Container, dass der Nutzer das Speichern der Änderungen bestätigt."""
        container.set_value(
            container_control_path,
            {"wantstore": wantstore},
        )
        log_info(__name__, f"set_wantstore({wantstore}): {container_control_path}")
        return True

    def save_all_values(
        path_name: str = container_data_path,
        control_path: str = container_control_path,
    ) -> bool:
        """
        Speichert alle relevanten Werte aus st.session_state in den Container.
        """
        try:
            if container is None:
                raise ValueError("Container is None.")
            log_info(
                __name__,
                f"Saving all values of '{path_name}' into container '{container.get_name()}' ...",
            )
            for key in st.session_state.keys():
                if key.startswith(path_name) or key.startswith(control_path):
                    container.set_value(key, st.session_state.get(key))
                    log_debug(
                        __name__, f"set_value('{key}', {st.session_state.get(key)})"
                    )
            log_info(
                __name__,
                f"Saved all values of '{path_name}' into container '{container.get_name()}'.",
            )
            return True
        except Exception as e:
            log_info(__name__, f"Error while saving values of '{path_name}': {e}")
            return False

    def create_callable(
        path_name: str = container_data_path,
        control_path: str = container_control_path,
    ) -> Callable[[], None]:
        """
        Gibt eine Callable zurück, die beim Auslösen alle Werte speichert.
        """

        def on_click() -> None:
            save_all_values(path_name=path_name, control_path=control_path)

        return on_click

    def default_value_for(item_schema: Dict[str, Any]) -> Any:
        """
        Liefert einen sinnvollen Standardwert basierend auf dem Typ im Schema.
        """
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

    def render_field(
        current_edited_data_path: str,
        field_name: str,
        field_def: Dict[str, Any],
        current_value: Any,
    ) -> Any:
        """
        Rendert ein einzelnes Eingabefeld in Streamlit basierend auf dem Feldschema.

        Args:
            current_edited_data_path (str): Der Pfad in st.session_state, der dem Feld entspricht.
            field_name (str): Name des Feldes.
            field_def (Dict[str, Any]): Das Schema des Feldes.
            current_value (Any): Aktueller Wert des Feldes.

        Returns:
            Any: Den vom Nutzer eingegebenen Wert.
        """
        field_type = field_def.get("type")
        if isinstance(field_type, list):
            field_type = field_type[0]  # Bei Mehrfachtypen wird der erste Typ gewählt.

        title = field_def.get("title")
        read_only = field_def.get("readOnly", False) == True
        write_only = (
            field_def.get("writeOnly", False) == True
        )  # z. B. für Passwortfelder
        example = field_def.get("example")
        deprecated = field_def.get("deprecated")
        description = field_def.get("description", "")
        if example:
            description += f", {_T('Example')}: {example}"
        if deprecated:
            description += f", {_T('Deprecated')}: {deprecated}"

        # Pfad und Label setzen
        if field_name.startswith("["):
            current_edited_data_path += f"{field_name}"
            label_name = field_name[1:-1]  # Entfernt eckige Klammern
        else:
            current_edited_data_path += f".{field_name}"
            label_name = field_name
        if title:
            label_name = title

        # Behandlung von Enums
        enum_values = field_def.get("enum")
        if enum_values:
            if current_value not in enum_values:
                current_value = enum_values[0]
            return st.selectbox(
                label=label_name,
                key=current_edited_data_path,
                options=enum_values,
                index=enum_values.index(current_value),
                help=description,
                disabled=read_only,
            )

        # Verschiedene Feldtypen rendern
        if field_type == "string":
            return st.text_input(
                label=label_name,
                value=current_value or "",
                key=current_edited_data_path,
                help=description,
                disabled=read_only,
            )

        elif field_type == "number":
            current_value = float(current_value) if current_value is not None else 0.0
            min_value = field_def.get("minimum")
            max_value = field_def.get("maximum")
            current_value = clamp_value(
                value=current_value,
                min_value=min_value,
                max_value=max_value,
            )
            return st.number_input(
                label=label_name,
                key=current_edited_data_path,
                value=current_value,
                min_value=min_value,
                max_value=max_value,
                help=description,
                disabled=read_only,
            )

        elif field_type == "integer":
            current_value = int(current_value) if current_value is not None else 0
            min_value = field_def.get("minimum")
            max_value = field_def.get("maximum")
            current_value = clamp_value(
                value=current_value,
                min_value=min_value,
                max_value=max_value,
            )
            return st.number_input(
                label=label_name,
                key=current_edited_data_path,
                value=current_value,
                min_value=min_value,
                max_value=max_value,
                step=1,
                help=description,
                disabled=read_only,
            )

        elif field_type == "boolean":
            return st.checkbox(
                label=label_name,
                key=current_edited_data_path,
                value=bool(current_value),
                help=description,
                disabled=read_only,
            )

        elif field_type == "array":
            if not isinstance(current_value, list):
                current_value = []
            items_def = field_def.get("items", {})

            with st.container(key=current_edited_data_path, border=True):
                st.write(f"### {label_name}")
                updated_list: List[Any] = []
                index = 0
                if len(current_value) == 0:
                    if st.button(
                        "➕", key=f"add_first_{index}_{current_edited_data_path}"
                    ):
                        save_all_values()
                        set_changed()
                        container.set_value(
                            path_name=current_edited_data_path, value=[]
                        )
                        container.insert(
                            path_name=current_edited_data_path,
                            index=index,
                            value=default_value_for(items_def),
                        )
                        st.rerun(scope="app")
                else:
                    while index < len(current_value):
                        current_val = current_value[index]
                        col1, col2, col3, col4 = st.columns([1, 20, 1, 1])
                        with col1:
                            if st.button(
                                "➕↑",
                                key=f"add_up_{index}_entry_in_{current_edited_data_path}",
                            ):
                                save_all_values()
                                set_changed()
                                container.insert(
                                    path_name=current_edited_data_path,
                                    index=index,
                                    value=default_value_for(items_def),
                                )
                                st.rerun()
                        with col2:
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
                                st.rerun()
                        with col4:
                            if st.button(
                                "➖",
                                key=f"remove_{index}_entry_of_{current_edited_data_path}",
                            ):
                                save_all_values()
                                set_changed()
                                container.pop(
                                    path_name=current_edited_data_path, index=index
                                )
                                st.rerun()
                        index += 1
                    return updated_list

        elif field_type == "object":
            with st.container(key=current_edited_data_path, border=True):
                return nestable(
                    current_edited_data_path=current_edited_data_path,
                    schema=field_def,
                    data=current_value,
                )

        else:
            # Fallback für unbekannte Typen
            return st.text_input(
                label=f"{label_name} (unhandled type: {field_type})",
                key=current_edited_data_path,
                value=str(current_value or ""),
                help=description,
                disabled=read_only,
            )

    def nestable(
        current_edited_data_path: str,
        schema: Dict[str, Any],
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Rendert ein verschachteltes Formular für Objekte basierend auf einem JSON-Schema.

        Args:
            current_edited_data_path (str): Pfad in st.session_state.
            schema (Dict[str, Any]): Das JSON-Schema.
            data (Dict[str, Any], optional): Vorhandene Daten. Standardmäßig {}.

        Returns:
            Dict[str, Any]: Vom Nutzer eingegebene Daten.
        """
        if data is None:
            data = {}
        if "title" in schema:
            st.title(schema["title"])

        user_data: Dict[str, Any] = {}
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

    # Hauptteil: Anzeige des Formulars
    log_info(__name__, f"Show edit form of '{label}'")
    st.markdown(f"**{label}**")

    schema = container.get_value(container_schema_path)
    data = container.get_value(container_data_path)
    if schema is None:
        raise ValueError(
            f"Schema is None: container '{container.get_name()}' path '{container_schema_path}'."
        )
    if data is None:
        raise ValueError(
            f"Data is None: container '{container.get_name()}' path '{container_data_path}'."
        )

    # Validierung der Daten ist optional; falls gewünscht, kann validate_json_data aufgerufen werden.
    # validate_json_data(data, schema)
    nestable(current_edited_data_path=container_data_path, schema=schema, data=data)

    if st.button(
        _T("OK"),
        icon=":material/thumb_up:",
        key=f"{container_control_path}.wantstore",
        on_click=create_callable(
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
