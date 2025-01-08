import logging
import logging.config
import os
import json

try:
    import yaml  # PyYAML library for YAML support
except ImportError:
    yaml = None


class CentralLogger:
    _instance = None  # Class variable for the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CentralLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = None):
        """
        Initializes central logging. If no configuration file exists,
        the default configuration is saved in the default file.
        """
        # Prevent __init__ from being executed multiple times
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Default configuration as a dictionary
        self.default_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "INFO",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "": {  # Root logger
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                }
            },
        }

        # Default path for the configuration file if not provided
        if config_path is None:
            config_path = os.path.expanduser("~/.offermee/logging_config.yaml")

        # Check if the configuration file exists, and create it if necessary
        if not os.path.exists(config_path):
            self._create_default_config_file(config_path)

        # Load the configuration from the file or fallback to default
        if config_path and os.path.exists(config_path):
            config = self.load_config(config_path)
            if config:
                logging.config.dictConfig(config)
            else:
                # If loading fails, use the default configuration
                logging.config.dictConfig(self.default_config)
        else:
            logging.config.dictConfig(self.default_config)

        self._initialized = True  # Mark the instance as initialized

    def _create_default_config_file(self, path: str):
        """
        Creates the default configuration file at the specified path,
        if it does not exist.
        """
        # Ensure the directory exists
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)

        try:
            # Save as YAML or JSON based on the file extension
            if path.endswith((".yaml", ".yml")) and yaml:
                with open(path, "w") as f:
                    yaml.dump(
                        self.default_config,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                    )
            elif path.endswith(".json"):
                with open(path, "w") as f:
                    json.dump(self.default_config, f, indent=4)
            else:
                # If YAML is not available and the file extension is YAML, try saving as JSON
                with open(path, "w") as f:
                    json.dump(self.default_config, f, indent=4)
            logging.info(f"Default logging configuration created: {path}")
        except Exception as e:
            logging.error(f"Error creating default configuration file: {e}")

    def load_config(self, path: str) -> dict:
        """
        Loads the configuration from a YAML or JSON file based on the file extension.
        Returns a configuration dictionary or None if loading fails.
        """
        try:
            if path.endswith((".yaml", ".yml")) and yaml:
                with open(path, "r") as f:
                    return yaml.safe_load(f)
            elif path.endswith(".json"):
                with open(path, "r") as f:
                    return json.load(f)
            else:
                logging.error(
                    f"Unsupported file format or missing YAML library for: {path}"
                )
        except Exception as e:
            logging.error(f"Error loading logging configuration: {e}")
        return None

    @staticmethod
    def getLogger(name: str) -> logging.Logger:
        """
        Returns a logger with the specified name.
        """
        if CentralLogger._instance is None:
            CentralLogger._instance = CentralLogger()
        return logging.getLogger(name)
