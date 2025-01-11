import os
import json
from jsonschema import validate, ValidationError
from offermee.logger import CentralLogger

# Verzeichnis, in dem die Schema-Dateien gespeichert sind
DEFAULT_JSON_SCHEMA_DIR = "offermee/schemas/json"

# Name der Schema-Datei
JSON_SCHEMA_FILENAME_CV = "cv.schema.json"

# Interner Speicher für das geladene Schema (Singleton)
_cv_schema = None

schema_logger = CentralLogger().getLogger(__name__)


def get_cv_schema():
    global _cv_schema
    if _cv_schema is None:
        schema_path = os.path.join(DEFAULT_JSON_SCHEMA_DIR, JSON_SCHEMA_FILENAME_CV)
        schema_logger.info(f"Loading cv json schema {schema_path}")
        try:
            with open(schema_path, "r", encoding="utf-8") as file:
                _cv_schema = json.load(file)
        except FileNotFoundError:
            schema_logger.error(f"Unable to find cv json schema {schema_path}")
            raise FileNotFoundError(f"Schema-Datei nicht gefunden: {schema_path}")
        except json.JSONDecodeError as e:
            schema_logger.error(f"Corrupted cv json schema {schema_path}")
            raise ValueError(f"Fehler beim Parsen des Schemas: {e}")
        except Exception as e:
            schema_logger.error(f"Unable to load cv json schema {schema_path}")
            raise ValueError(f"Unable to load cv json schema {schema_path}")

    return _cv_schema


def validate_json(json, schema):
    # Validierung der restlichen Daten gegen das Schema
    try:
        validate(instance=json, schema=schema)
    except ValidationError as e:
        schema_logger.error(
            f"Validation error for json {json} against schema {schema}: {e}"
        )
