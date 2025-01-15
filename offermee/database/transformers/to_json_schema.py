from typing import Any, Dict, Type
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import Column, Integer, String, Float, Boolean, Enum


def db_model_to_json_schema(model: Type[DeclarativeMeta]) -> Dict[str, Any]:
    """
    Generate a JSON schema from a SQLAlchemy ORM model.

    Args:
        model (Type[DeclarativeMeta]): SQLAlchemy model class.

    Returns:
        Dict[str, Any]: JSON schema representation of the model.
    """
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
        elif isinstance(column.type, Float):
            field_schema["type"] = "number"
        elif isinstance(column.type, String):
            field_schema["type"] = "string"
        elif isinstance(column.type, Boolean):
            field_schema["type"] = "boolean"
        elif isinstance(column.type, Enum):
            field_schema["type"] = "string"
            field_schema["enum"] = [e.value for e in column.type.enums]
        else:
            field_schema["type"] = "string"  # Fallback type

        # Add constraints if present
        if column.default is not None:
            field_schema["default"] = (
                str(column.default.arg)
                if callable(column.default.arg)
                else column.default.arg
            )
        if column.nullable is False:
            schema["required"].append(field_name)
        if hasattr(column.type, "length") and column.type.length:
            field_schema["maxLength"] = column.type.length

        schema["properties"][field_name] = field_schema

    return schema
