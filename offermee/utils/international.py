import os
import gettext
from offermee.utils.logger import CentralLogger

international_logger = CentralLogger.getLogger("international")

current_language = "de"  # Beispiel: Deutsch
locales_dir = os.path.join(os.path.dirname(__file__), "..", "..", "locales")

try:
    translations = gettext.translation(
        domain="messages",
        localedir=locales_dir,
        languages=[current_language],
    )
    translations.install()
    _T = translations.gettext
    international_logger.info(f"Loaded translations for language: {current_language}")
except FileNotFoundError:
    international_logger.warning(
        f"No translation file found for language: {current_language}"
    )
    # Fallback: Verwenden Sie die Standard-Gettext-Installation ohne spezifische Übersetzungen
    gettext.install("messages", localedir=locales_dir)
    _T = gettext.gettext
except Exception as e:
    international_logger.error(f"Error loading translations: {e}")
    gettext.install("messages", localedir=locales_dir)
    _T = gettext.gettext
