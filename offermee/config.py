import os
import logging
import streamlit as st
from offermee.local_settings import LocalSettings
from offermee.logger import CentralLogger


class Config:
    CURRENT_LOGGED_IN: str = False
    CURRENT_USER: str = None
    AI_FAMILIES: list = []
    AI_SELECTED_FAMILY: str = None
    SENDER_EMAIL: str = None
    SENDER_PASSWORD: str = None
    SMTP_SERVER: str = None
    SMTP_PORT: str = None
    _instance: str = None

    @staticmethod
    def get_instance():
        if Config._instance is None:
            Config._instance = Config()
        return Config._instance

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
            logging.info("Creating a new instance of Config")
        return cls._instance

    @staticmethod
    def __reset__():
        Config.CURRENT_LOGGED_IN = False
        Config.CURRENT_USER = None
        Config.AI_FAMILIES = []
        Config.AI_SELECTED_FAMILY = None
        Config.SENDER_EMAIL = None
        Config.SENDER_PASSWORD = None
        Config.SMTP_SERVER = None
        Config.SMTP_PORT = None

    def __init__(self):
        if not hasattr(self, "initialized"):  # Prevents multiple initializations
            self.logger = CentralLogger.getLogger(name=__name__)
            self.initialized = True  # Marks as initialized

    def init_current_config(self, logged_in=False, username=None):
        """
        Returns the current configuration depending on whether a user is logged in or not.
        """

        # 1) Check if a user is logged in:
        if logged_in != True:
            # No user logged in -> empty config
            Config.__reset__()
            return
        # 2) Load RSA key paths from environment variables
        RSA_PUBLIC_KEY_PATH = os.getenv("OE_PUK")
        RSA_PRIVATE_KEY_PATH = os.getenv("OE_PRK")
        # 3) If a user is logged in:
        #    => Initialize LocalSettings with RSA key paths and load encrypted .settings
        settings = LocalSettings(
            public_key_path=RSA_PUBLIC_KEY_PATH,
            private_key_path=RSA_PRIVATE_KEY_PATH,
            username=username,
        )
        settings.load_settings()

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
        Config.CURRENT_USER = username
        Config.AI_FAMILIES = settings.get("ai_families", {})
        Config.AI_SELECTED_FAMILY = settings.get("ai_selected_family", "")
        Config.SENDER_EMAIL = settings.get("email_address", "")
        Config.SENDER_PASSWORD = settings.get("email_password", "")
        Config.SMTP_SERVER = settings.get("smtp_server", "smtp.gmail.com")
        Config.SMTP_PORT = settings.get("smtp_port", 465)
        return

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
