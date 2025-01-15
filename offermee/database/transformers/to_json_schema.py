import enum
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import Column, Integer, String, Float, Boolean, Enum as SAEnum
from sqlalchemy.types import DateTime, Text, Date
from typing import Any, Dict, Type


def db_model_to_json_schema(model: Type[DeclarativeMeta]) -> Dict[str, Any]:
    """
    Generate a JSON schema from a SQLAlchemy ORM model.

    Args:
        model (Type[DeclarativeMeta]): SQLAlchemy model class.

    Returns:
        Dict[str, Any]: JSON schema representation of the model.
    """

    def get_default_value_as_string(default_obj) -> Any:
        """
        Konvertiert das default_obj (z. B. ColumnDefault, ScalarElementColumnDefault, etc.)
        in einen JSON-serialisierbaren Wert (String/Float/Int etc.).
        """
        if default_obj is None:
            return None
        # Bei ColumnDefault/ScalarElementColumnDefault liegt das echte Objekt oft in `arg`
        arg = getattr(default_obj, "arg", default_obj)
        # callable => z.B. datetime.utcnow
        if callable(arg):
            return str(arg)
        # Falls es sich tatsächlich um ein Enum-Objekt handelt
        if isinstance(arg, enum.Enum):
            return arg.value
        return arg  # Letzte Instanz: einfach den Wert zurückgeben (idR int, float, str)

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": model.__name__,
        "type": "object",
        "properties": {},
        "required": [],
    }

    for column in model.__table__.columns:
        field_name = column.name
        field_schema = {}

        # Map SQLAlchemy column types to JSON Schema types
        if isinstance(column.type, Integer):
            field_schema["type"] = "integer"
        elif isinstance(column.type, SAEnum) or hasattr(column.type, "enums"):
            field_schema["type"] = "string"
            field_schema["enum"] = column.type.enums
        elif isinstance(column.type, Float):
            field_schema["type"] = "number"
        elif isinstance(column.type, String) or isinstance(column.type, Text):
            field_schema["type"] = "string"
        elif isinstance(column.type, Boolean):
            field_schema["type"] = "boolean"
        elif isinstance(column.type, DateTime) or isinstance(column.type, Date):
            field_schema["type"] = "string"  # ISO8601 string
        else:
            field_schema["type"] = "string"  # Fallback type

        # Add default value if present
        if column.default is not None:
            default_value = get_default_value_as_string(column.default)
            if default_value is not None:
                field_schema["default"] = default_value

        # Add "required" if not nullable
        if not column.nullable:
            schema["required"].append(field_name)

        # Add maxLength if string has a length
        if hasattr(column.type, "length") and column.type.length:
            field_schema["maxLength"] = column.type.length

        schema["properties"][field_name] = field_schema

    return schema
