import os
import json
from jsonschema import validate, ValidationError
from offermee.utils.logger import CentralLogger
from offermee.schemas.json.schema_keys import SchemaKey

# Directory where schema files are stored
DEFAULT_JSON_SCHEMA_DIR = "offermee/schemas/json"

# Schema file names
JSON_SCHEMA_FILENAME_CV = "cv.schema.json"
JSON_SCHEMA_FILENAME_PROJECT = "project.schema.json"

# Internal storage for loaded schemas (Singleton)
_schemas = {
    SchemaKey.CV: {"filename": JSON_SCHEMA_FILENAME_CV, "value": None},
    SchemaKey.PROJECT: {"filename": JSON_SCHEMA_FILENAME_PROJECT, "value": None},
}

schema_logger = CentralLogger.getLogger(__name__)


def get_schema(schema_key: SchemaKey):
    """
    Retrieve and load a JSON schema based on the provided schema key.

    Valid values for schema_key:
      - SchemaKey.CV
      - SchemaKey.PROJECT

    This function will load the schema from disk on the first request and cache it
    for subsequent calls. If the schema is already loaded, it returns the cached version.

    Parameters:
    - schema_key (SchemaKey): The key identifying which schema to load.

    Returns:
    - dict: The loaded JSON schema as a Python dictionary.

    Raises:
    - ValueError: If the provided schema_key is not defined.
    - FileNotFoundError: If the schema file cannot be found.
    - ValueError: If the schema file is corrupted or cannot be parsed.
    - RuntimeError: For any other errors encountered while loading the schema.
    """
    global _schemas
    schema_entry = _schemas.get(schema_key)

    if schema_entry is None:
        schema_logger.error(f"Schema '{schema_key}' is not defined.")
        raise ValueError(f"Schema '{schema_key}' is not defined.")

    # Check if the schema has already been loaded
    if schema_entry["value"] is None:
        schema_path = os.path.join(DEFAULT_JSON_SCHEMA_DIR, schema_entry["filename"])
        schema_logger.info(
            f"Loading '{schema_key}' JSON schema from '{schema_path}' ..."
        )
        try:
            with open(schema_path, "r", encoding="utf-8") as file:
                schema_entry["value"] = json.load(file)
        except FileNotFoundError:
            schema_logger.error(
                f"Unable to find '{schema_key}' JSON schema at '{schema_path}'"
            )
            raise FileNotFoundError(f"Schema file not found: '{schema_path}'")
        except json.JSONDecodeError as e:
            schema_logger.error(
                f"Corrupted '{schema_key}' JSON schema at '{schema_path}': {e}"
            )
            raise ValueError(f"Error parsing schema: {e}")
        except Exception as e:
            schema_logger.error(
                f"Unable to load '{schema_key}' JSON schema from '{schema_path}': {e}"
            )
            raise RuntimeError(
                f"Unable to load '{schema_key}' JSON schema from '{schema_path}': {e}"
            )

    schema_logger.info(f"Loaded '{schema_key}' JSON schema.")
    return schema_entry["value"]


def validate_json(json_data, schema):
    """
    Validate the provided JSON data against the given schema.

    Parameters:
    - json_data: The JSON data to validate.
    - schema: The JSON schema to validate against.

    Raises:
    - ValidationError: If validation fails.
    """
    try:
        validate(instance=json_data, schema=schema)
    except ValidationError as e:
        schema_logger.error(
            f"Validation error for JSON {json_data} against schema {schema}: {e}"
        )
        raise  # Optionally re-raise the exception or handle it accordingly
