import enum
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import Integer, String, Float, Boolean, Enum as SAEnum
from sqlalchemy.types import DateTime, Text, Date
from typing import Any, Dict, Type


import enum
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import Integer, String, Float, Boolean, Enum as SAEnum
from sqlalchemy.types import DateTime, Text, Date
from typing import Any, Dict, Type, Callable


def db_model_to_json_schema(model: Type[DeclarativeMeta]) -> Dict[str, Any]:
    """
    Erzeugt ein JSON-Schema aus einem SQLAlchemy ORM Model.

    Unterstützt werden u. a. zusätzliche Informationen aus der Spalten-info,
    z. B. "title", "description", "default", "example", "deprecated",
    "readOnly" und "writeOnly".

    Args:
        model (Type[DeclarativeMeta]): SQLAlchemy Model-Klasse.

    Returns:
        Dict[str, Any]: JSON-Schema-Repräsentation des Models.
    """

    def get_default_value_as_string(default_obj: Any) -> Any:
        """
        Konvertiert ein Default-Objekt (z. B. ColumnDefault, ScalarElementColumnDefault, etc.)
        in einen JSON-serialisierbaren Wert (z. B. str, int, float).

        Args:
            default_obj (Any): Das Default-Objekt der Spalte.

        Returns:
            Any: Der konvertierte Standardwert oder None.
        """
        if default_obj is None:
            return None
        # Bei ColumnDefault/ScalarElementColumnDefault liegt der eigentliche Wert oft in `arg`
        arg = getattr(default_obj, "arg", default_obj)
        # Falls callable (z. B. datetime.utcnow) – Rückgabe als String-Repräsentation
        if callable(arg):
            return str(arg)
        # Falls es sich um ein Enum-Objekt handelt, den zugehörigen Wert zurückgeben
        if isinstance(arg, enum.Enum):
            return arg.value
        return arg  # Bei int, float, str etc.

    def map_column_type_to_json_type(column: Any) -> Dict[str, Any]:
        """
        Ordnet den SQLAlchemy-Spaltentyp einem JSON-Schema-Typ zu.

        Args:
            column (Any): Die SQLAlchemy-Spalte.

        Returns:
            Dict[str, Any]: Ein Dictionary mit dem Schlüssel "type" und ggf. weiteren Attributen.
        """
        col_type = column.type
        if isinstance(col_type, Integer):
            return {"type": "integer"}
        elif isinstance(col_type, SAEnum) or hasattr(col_type, "enums"):
            return {"type": "string", "enum": col_type.enums}
        elif isinstance(col_type, Float):
            return {"type": "number"}
        elif isinstance(col_type, (String, Text)):
            schema = {"type": "string"}
            # Falls Länge angegeben ist, als maxLength übernehmen
            if hasattr(col_type, "length") and col_type.length:
                schema["maxLength"] = col_type.length
            return schema
        elif isinstance(col_type, Boolean):
            return {"type": "boolean"}
        elif isinstance(col_type, (DateTime, Date)):
            return {"type": "string", "format": "date-time"}  # ISO8601-Format
        else:
            return {"type": "string"}  # Fallback

    def set_schema_attributes(field_schema: Dict[str, Any], column: Any) -> None:
        """
        Überschreibt bzw. ergänzt das Feld-Schema anhand von Zusatzinformationen
        aus der Spalten-info sowie Default-Werten und Kommentaren.

        Args:
            field_schema (Dict[str, Any]): Das bereits generierte Feld-Schema.
            column (Any): Die SQLAlchemy-Spalte.
        """
        # Mapping von Info-Schlüsseln zu JSON-Schema-Schlüsseln
        mapping: Dict[str, str] = {
            "label": "title",
            "title": "title",
            "description": "description",
            "read_only": "readOnly",
            "write_only": "writeOnly",
            "deprecated": "deprecated",
            "example": "example",
        }
        info = getattr(column, "info", None)
        if info:
            for key, value in info.items():
                target_key = mapping.get(key)
                if target_key:
                    field_schema[target_key] = value

        # Default-Wert verarbeiten
        if getattr(column, "default", None) is not None:
            default_value = get_default_value_as_string(column.default)
            if default_value is not None:
                field_schema["default"] = default_value

        # Falls keine Beschreibung in info gesetzt wurde, kann der Spaltenkommentar genutzt werden
        if (
            "description" not in field_schema
            and getattr(column, "comment", None) is not None
        ):
            field_schema["description"] = column.comment

    # Initiales JSON-Schema
    schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": model.__name__,
        "type": "object",
        "properties": {},
        "required": [],
    }

    # Iteriere über alle Spalten des Models
    for column in model.__table__.columns:
        field_name = column.name
        # Erstelle zunächst das Schema anhand des Spaltentyps
        field_schema = map_column_type_to_json_type(column)
        # Ergänze Schema-Attribute aus der Spalten-info, Default-Werten, etc.
        set_schema_attributes(field_schema, column)
        # Falls die Spalte nicht nullable ist, als erforderlich markieren
        if not column.nullable:
            schema["required"].append(field_name)
        schema["properties"][field_name] = field_schema

    return schema


from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import DeclarativeMeta
from typing import Dict, Any, Set, Type


def build_full_json_schema(
    model: Type[DeclarativeMeta], visited: Set[Type[DeclarativeMeta]] = None
) -> Dict[str, Any]:
    """
    Recursively build a JSON schema for a model, including its relationships.
    This inlines the child schema for each relationship.

    WARNING: If your models have deep or cyclical relationships, this can blow up in size
             or cause infinite recursion. The `visited` set helps avoid infinite loops,
             but repeated references to the same model are inlined more than once
             (unless you skip or add references).
    """
    if visited is None:
        visited = set()

    # If we've already seen this model, return an empty or minimal schema
    # to avoid infinite recursion. In a more advanced implementation,
    # you might return {"$ref": "#/definitions/<ModelName>"} instead.
    if model in visited:
        return {"type": "object", "title": model.__name__ + " (Already Included)"}

    visited.add(model)

    # 1) Start with the base schema (columns only).
    base_schema = db_model_to_json_schema(model)

    # 2) For each relationship in the model, build child schema.
    mapper = inspect(model)
    for rel_name in mapper.relationships.keys():
        rel_prop = getattr(model, rel_name).property
        related_model = rel_prop.mapper.class_  # e.g. Child class
        child_schema = build_full_json_schema(related_model, set(visited))
        # print(f"{rel_prop} uselist? {rel_prop.uselist}")
        if rel_prop.uselist:
            # This is a one-to-many or many-to-many relationship
            # so we represent it as an array of objects.
            base_schema["properties"][rel_name] = {
                "type": "array",
                "items": child_schema,
            }
        else:
            # This is a many-to-one or one-to-one relationship
            # so we represent it as a nested object.
            base_schema["properties"][rel_name] = child_schema

    return base_schema
