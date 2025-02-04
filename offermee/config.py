import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv
from platformdirs import (
    site_data_dir,
    site_config_dir,
    site_cache_dir,
    user_data_dir,
    # site_log_dir,
    user_log_dir,
    user_runtime_dir,
)
import tempfile

from offermee.AI.ai_manager import AIManager
from offermee.local_settings import LocalSettings
from offermee.logger import CentralLogger


APP_NAME = "OfferMee"
# Set to False to avoid additional nesting on Windows (e.g. "MyCompany" folder).
# If you prefer "OfferMee" or your company name as an author folder, set to a string.
APP_AUTHOR = False


@dataclass
class ConfigData:
    """
    Holds configuration fields in a structured way.
    """

    logged_in: bool = False
    current_user: str = None

    ai_families: dict = field(default_factory=dict)
    ai_selected_family: str = None

    sender_email: str = None
    sender_password: str = None
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465

    imap_email: str = None
    imap_password: str = None
    imap_server: str = "imap.gmail.com"
    imap_port: int = 993

    rfp_mailbox = "RFPs"
    rfp_email_subject_filter = "RFP"
    rfp_email_sender_filter = "partner@example.com"

    def __init__(self):
        self.clear()

    def __reset__(self):
        """
        Resets the configuration fields.
        """
        self.logged_in = False
        self.current_user = None
        self.ai_families = {}
        self.ai_selected_family = None
        self.sender_email = None
        self.sender_password = None
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465
        self.imap_email = None
        self.imap_password = None
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.rfp_mailbox = "RFPs"
        self.rfp_email_subject_filter = "RFP"
        self.rfp_email_sender_filter = ""

    def clear(self):
        """
        Clears the configuration fields.
        """
        self.__reset__()


class Config:
    """
    Central configuration class for the OfferMee project (Singleton).

    Responsibilities:
    - Manages login status and current user (ConfigData).
    - Loads and holds settings (both local and environment-based).
    - Manages email and AI-related configuration.
    - Provides paths for central and user-specific databases.
    - Now also provides getters for log, data, config, runtime, cache, and temp folders via platformdirs.
    """

    # Singleton instance
    _instance = None

    def __new__(cls):
        """
        Singleton pattern implementation:
        Creates an instance only once.
        """
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
            logging.info("Creating a new instance of Config")
        return cls._instance

    @staticmethod
    def get_instance() -> "Config":
        """
        Static method to retrieve the Singleton instance.
        """
        if Config._instance is None:
            Config._instance = Config()
        return Config._instance

    def __init__(self):
        """
        Constructor:
        - Initializes the logger
        - Marks the instance as initialized
        - Sets LocalSettings to None (will be loaded later if a user is logged in)
        - Creates a new ConfigData object to hold config fields.
        """
        if not hasattr(self, "initialized"):
            self.logger = CentralLogger.getLogger(name=__name__)
            self.local_settings: LocalSettings = None
            # New unified data container:
            self.config_data = ConfigData()
            self.initialized = True

    def __reset__(self):
        """
        Resets the configuration, e.g. when no user is logged in.
        """
        self.logger.info("Resetting Config")
        self.local_settings = None

        # Reset dataclass fields
        self.config_data.clear

        AIManager().set_default_client()
        self.logger.info("Config reset.")

    def init_current_config(self, logged_in: bool = False, username: str = None):
        """
        Initializes the configuration depending on whether a user is logged in.

        :param logged_in: True if a user is logged in, otherwise False.
        :param username: The username of the currently logged-in user.
        """
        if not logged_in:
            # No user logged in -> reset config
            self.__reset__()
            return

        # User is logged in -> load .env and read RSA key paths
        load_dotenv()
        RSA_PUBLIC_KEY_PATH = os.path.expanduser(os.getenv("OE_PUK"))
        RSA_PRIVATE_KEY_PATH = os.path.expanduser(os.getenv("OE_PRK"))

        # Create LocalSettings instance and load settings
        self.local_settings = LocalSettings(
            public_key_path=RSA_PUBLIC_KEY_PATH,
            private_key_path=RSA_PRIVATE_KEY_PATH,
            username=username,
        )
        self.reload_settings(username=username)
        self.logger.info(f"Config initialized for user {username}")

    def reload_settings(self, username: str = None):
        """
        Reloads settings from the LocalSettings file and updates
        both ConfigData and the old static class variables (if present).

        :param username: The username to set (if provided).
        :raises ValueError: if self.local_settings is None.
        """
        if not self.local_settings:
            self.logger.error("LocalSettings is None, cannot reload settings.")
            raise ValueError(
                "LocalSettings is None. Make sure to call init_current_config first."
            )

        self.logger.info("Reloading settings...")
        self.local_settings.load_settings()

        # Update dataclass fields
        self.config_data.logged_in = True
        self.config_data.current_user = username or self.config_data.current_user
        self.config_data.ai_families = self.local_settings.get("ai_families", {})
        self.config_data.ai_selected_family = self.local_settings.get(
            "ai_selected_family", ""
        )
        self.config_data.sender_email = self.local_settings.get("email_address", "")
        self.config_data.sender_password = self.local_settings.get("email_password", "")
        self.config_data.smtp_server = self.local_settings.get(
            "smtp_server", ""  # smtp.gmail.com"
        )
        self.config_data.smtp_port = self.local_settings.get("smtp_port", 465)
        self.config_data.imap_email = self.local_settings.get("receiver_email", "")
        self.config_data.imap_password = self.local_settings.get(
            "receiver_password", ""
        )
        self.config_data.imap_server = self.local_settings.get(
            "receiver_server", ""  # "imap.gmail.com"
        )
        self.config_data.imap_port = self.local_settings.get("receiver_port", 993)
        self.config_data.rfp_mailbox = self.local_settings.get("rfp_mailbox", "RFPs")
        self.config_data.rfp_email_subject_filter = self.local_settings.get(
            "rfp_email_subject_filter", "RFP"
        )
        self.config_data.rfp_email_sender_filter = self.local_settings.get(
            "rfp_email_sender_filter", ""
        )

        # Initialize AIManager with the newly loaded values
        AIManager().set_default_client(
            self.config_data.ai_selected_family,
            data=self.config_data.ai_families.get(
                self.config_data.ai_selected_family, {}
            ),
        )
        self.logger.info("Settings reloaded.")

    # ------------------------------------------------
    # New recommended approach: Access to ConfigData
    # ------------------------------------------------

    def get_config_data(self) -> ConfigData:
        """
        Returns the ConfigData object that consolidates
        all configuration fields.

        This is the recommended interface going forward.
        """
        return self.config_data

    # ------------------------------------------------
    # Central Folders (server scenario)
    # ------------------------------------------------

    def get_central_db_dir(self) -> str:
        """
        Returns the db path to the central database (e.g., /var/lib/offermee/dbs).
        """
        path = os.path.join(self.get_central_data_dir(), "dbs")
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created central db directory: {path}")
        return path

    def get_central_log_dir(self) -> str:
        """
        Returns the platform-specific site-wide log directory.
        """
        path = user_log_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created central log directory: {path}")
        return path

    def get_central_data_dir(self) -> str:
        """
        Returns the platform-specific site-wide data directory.
        E.g. on Linux: /usr/local/share/OfferMee
             on Windows: C:\\ProgramData\\OfferMee
        """
        path = site_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created central data directory: {path}")
        return path

    def get_central_config_dir(self) -> str:
        """
        Returns the platform-specific site-wide config directory.
        E.g. on Linux: /etc/xdg/OfferMee
             on Windows: C:\\ProgramData\\OfferMee\\Config
        """
        path = site_config_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created central config directory: {path}")
        return path

    def get_central_cache_folder(self) -> str:
        """
        Returns the platform-specific site-wide cache directory.
        E.g. on Linux: /var/cache/OfferMee
             on Windows: C:\\ProgramData\\OfferMee\\Cache
        """
        path = site_cache_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created central cache directory: {path}")
        return path

    # ------------------------------------------------
    # User Folders (server scenario)
    # ------------------------------------------------

    def get_user_data_dir(self) -> str:
        """
        Returns a platform-specific directory path for OfferMee.
        """
        path = user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created user data directory: {path}")
        return path

    def get_user_temp_dir(self) -> str:
        """
        Returns a platform-agnostic temporary directory path for OfferMee.
        Since platformdirs does not provide a site_temp_dir, we can default
        to the system temp folder (tempfile.gettempdir()).
        E.g. on Linux: /tmp
             on Windows: C:\\Users\\<User>\\AppData\\Local\\Temp
        """
        path = tempfile.gettempdir()
        path = os.path.join(path, "OfferMee")
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created user temp directory: {path}")
        return path

    def get_user_runtime_dir(self) -> str:
        """
        Returns a 'runtime' directory for the user.
        """
        path = user_runtime_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
        if not os.path.exists(path=path):
            os.makedirs(path)
            logging.info(f"Created user runtime directory: {path}")
        return path

    # ------------------------------------------------
    # Old getters - (if needed, marked as deprecated)
    # ------------------------------------------------

    def get_ai_families(self) -> dict:
        """
        Deprecated. Use self.config_data.ai_families instead, or get_config_data().
        """
        return self.config_data.ai_families

    def get_ai_selected_family(self) -> str:
        """
        Deprecated. Use self.config_data.ai_selected_family instead, or get_config_data().
        """
        return self.config_data.ai_selected_family

    def get_ai_family(self, family) -> dict:
        """
        Deprecated. Use self.config_data.ai_families[family] or get_config_data().
        """
        return self.config_data.ai_families.get(family, {})

    def get_ai_family_api_key(self, family) -> str:
        """
        Deprecated. Use self.config_data.ai_families[family]['api_key'] or get_config_data().
        """
        return self.config_data.ai_families.get(family, {}).get("api_key", "")

    def get_ai_family_model(self, family) -> str:
        """
        Deprecated. Use self.config_data.ai_families[family]['model'] or get_config_data().
        """
        return self.config_data.ai_families.get(family, {}).get("model", "")

    def get_sender_email(self) -> str:
        """
        Deprecated. Use self.config_data.sender_email instead, or get_config_data().
        """
        return self.config_data.sender_email

    def get_sender_password(self) -> str:
        """
        Deprecated. Use self.config_data.sender_password instead, or get_config_data().
        """
        return self.config_data.sender_password

    def get_smtp_server(self) -> str:
        """
        Deprecated. Use self.config_data.smtp_server instead, or get_config_data().
        """
        return self.config_data.smtp_server

    def get_smtp_port(self) -> int:
        """
        Deprecated. Use self.config_data.smtp_port instead, or get_config_data().
        """
        return self.config_data.smtp_port

    # ------------------------------------------------
    # User and Settings
    # ------------------------------------------------

    def get_current_user(self) -> str:
        """
        Deprecated. Use self.config_data.current_user or get_config_data().
        """
        return self.config_data.current_user

    def is_logged_in(self) -> bool:
        """
        Returns True if a valid user is logged in; Otherwise False.
        """
        return self.config_data.logged_in

    def get_local_settings(self) -> LocalSettings:
        """
        Returns the LocalSettings instance (if any).
        """
        return self.local_settings

    def get_local_settings_to_dict(self) -> dict:
        """
        Returns the local settings as a dictionary,
        or an empty dict if local_settings is None.
        """
        return self.local_settings.to_dict() if self.local_settings else {}

    def get_name_from_local_settings(self) -> str:
        """
        Retrieves first_name and last_name from local settings (if present).
        """
        settings_dict = self.get_local_settings_to_dict()
        first_name = settings_dict.get("first_name", "")
        last_name = settings_dict.get("last_name", "")
        return f"{first_name} {last_name}".strip()

    def save_local_settings(self, settings: dict):
        """
        Saves new settings in local_settings (encrypted).

        :param settings: Dict containing the new setting values.
        :raises ValueError: if self.local_settings is None.
        """
        if self.local_settings:
            self.local_settings.save_settings(new_settings=settings)
        else:
            self.logger.error(
                "No LocalSettings instance available. "
                "Check environment paths to OE_PUK and OE_PRK or log in first."
            )
            raise ValueError("No LocalSettings instance available.")
