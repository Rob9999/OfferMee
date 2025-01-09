import os
import logging
from dotenv import load_dotenv
import streamlit as st
from offermee.AI.ai_manager import AIManager
from offermee.local_settings import LocalSettings
from offermee.logger import CentralLogger


class Config:
    CURRENT_LOGGED_IN: str = False
    CURRENT_USER: str = None
    AI_FAMILIES: dict = {}
    AI_SELECTED_FAMILY: str = None
    SENDER_EMAIL: str = None
    SENDER_PASSWORD: str = None
    SMTP_SERVER: str = None
    SMTP_PORT: str = None
    _instance: str = None

    @staticmethod
    def get_instance() -> "Config":
        if Config._instance is None:
            Config._instance = Config()
        return Config._instance

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
            logging.info("Creating a new instance of Config")
        return cls._instance

    def __reset__(self):
        self.logger.info("Resetting Config")
        self.local_settings = None
        Config.CURRENT_LOGGED_IN = False
        Config.CURRENT_USER = None
        Config.AI_FAMILIES = {}
        Config.AI_SELECTED_FAMILY = None
        Config.SENDER_EMAIL = None
        Config.SENDER_PASSWORD = None
        Config.SMTP_SERVER = None
        Config.SMTP_PORT = None
        AIManager().set_default_client()
        self.logger.info("Config reset.")

    def __init__(self):
        if not hasattr(self, "initialized"):  # Prevents multiple initializations
            self.logger = CentralLogger.getLogger(name=__name__)
            self.local_settings: LocalSettings = None
            self.initialized = True  # Marks as initialized

    def init_current_config(self, logged_in=False, username=None):
        """
        Returns the current configuration depending on whether a user is logged in or not.
        """
        # 1) Check if a user is logged in:
        if logged_in != True:
            # No user logged in -> empty config
            self.__reset__()
            return
        # 2) Load RSA key paths from environment variables
        load_dotenv()
        RSA_PUBLIC_KEY_PATH = os.path.expanduser(os.getenv("OE_PUK"))
        RSA_PRIVATE_KEY_PATH = os.path.expanduser(os.getenv("OE_PRK"))
        # 3) If a user is logged in:
        #    => Initialize LocalSettings with RSA key paths and load encrypted .settings
        self.local_settings = LocalSettings(
            public_key_path=RSA_PUBLIC_KEY_PATH,
            private_key_path=RSA_PRIVATE_KEY_PATH,
            username=username,
        )
        self.reload_settings(username=username)
        self.logger.info(f"Config initialized for user {username}")
        return

    def reload_settings(self, username: str = None):

        self.logger.info("Reloading settings...")
        self.local_settings.load_settings()

        # The settings file can look like this (as JSON):
        # {
        #   "email_address": "user@example.com",
        #   "email_password": "secretpass",
        #   "ai_selected_family": "openai",
        #   "ai_families": {
        #       "openai": {
        #           "api_key": "sk-XXXXXX...",
        #           "model": "gpt-4"
        #       },
        #       "genai": {
        #           "api_key": "AIzaSy...",
        #           "model": "gemini-1.5-flash"
        #       }
        #   }
        #   ... other fields ...
        # }

        # Now build the final configuration
        Config.CURRENT_LOGGED_IN = True
        Config.CURRENT_USER = username or Config.CURRENT_USER
        Config.AI_FAMILIES = self.local_settings.get("ai_families", {})
        Config.AI_SELECTED_FAMILY = self.local_settings.get("ai_selected_family", "")
        Config.SENDER_EMAIL = self.local_settings.get("email_address", "")
        Config.SENDER_PASSWORD = self.local_settings.get("email_password", "")
        Config.SMTP_SERVER = self.local_settings.get("smtp_server", "smtp.gmail.com")
        Config.SMTP_PORT = self.local_settings.get("smtp_port", 465)
        AIManager().set_default_client(
            Config.AI_SELECTED_FAMILY,
            data=Config.AI_FAMILIES.get(Config.AI_SELECTED_FAMILY, {}),
        )
        self.logger.info("Settings reloaded.")

    def get_ai_families(self) -> list:
        return Config.AI_FAMILIES

    def get_ai_selected_family(self) -> str:
        return Config.AI_SELECTED_FAMILY

    def get_ai_family(self, family) -> dict:
        return Config.AI_FAMILIES.get(family, {})

    def get_ai_family_api_key(self, family) -> dict:
        return Config.AI_FAMILIES.get(family, {}).get("api_key", "")

    def get_ai_family_model(self, family) -> dict:
        return Config.AI_FAMILIES.get(family, {}).get("model", "")

    def get_sender_email(self) -> str:
        return Config.SENDER_EMAIL

    def get_sender_password(self) -> str:
        return Config.SENDER_PASSWORD

    def get_smtp_server(self) -> str:
        return Config.SMTP_SERVER

    def get_smtp_port(self) -> int:
        return Config.SMTP_PORT

    def get_current_user(self) -> str:
        return Config.CURRENT_USER

    def is_logged_in(self) -> bool:
        return Config.CURRENT_LOGGED_IN

    def get_local_settings(self) -> LocalSettings:
        return self.local_settings

    def get_local_settings_to_dict(self) -> dict:
        return self.local_settings.to_dict()

    def get_name_from_local_settings(self):
        local_settings = self.get_local_settings_to_dict()
        return local_settings.get("first_name") + " " + local_settings.get("last_name")

    def save_local_settings(self, settings: dict):
        if self.local_settings:
            self.local_settings.save_settings(new_settings=settings)
        else:
            self.logger.error(
                "No LocalSettings instance available, check environment paths to OE_PUK and OE_PRK or log in first."
            )
            raise ValueError("No LocalSettings instance available.")
