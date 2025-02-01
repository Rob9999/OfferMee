import enum
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import Integer, String, Float, Boolean, Enum as SAEnum
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
