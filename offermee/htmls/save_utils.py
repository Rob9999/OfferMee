import os
from urllib.parse import urlparse
import re

from offermee.utils.config import Config
from offermee.utils.logger import CentralLogger

save_utils_logger = CentralLogger.getLogger(__name__)


def sanitize_filename(filename):
    """Bereinigt den Dateinamen, um unerlaubte Zeichen zu entfernen."""
    return re.sub(r"[^\w\-]", "_", filename)


def save_html(html, filename: str, folder: str = "./saved_html"):
    """
    Speichert HTML-Inhalt auf der Festplatte im Anwender Verzeichnis ~/{folder}.

    Args:
        html (bytes): Der HTML-Inhalt als Bytes.
        filename (str): Der Name der Datei.
        folder (str): Der Zielordner im Anwenderverzeichnis (Standard: "./saved_html").
    """
    save_utils_logger.info(f"Saving html to '{filename}' (folder='~/{folder}') ...")
    try:

        save_folder = os.path.join(Config.get_instance().get_user_data_dir(), folder)
        # Erstelle den Zielordner, falls er nicht existiert
        os.makedirs(save_folder, exist_ok=True)

        # Vollständigen Pfad erstellen
        filepath = os.path.join(save_folder, filename)

        # HTML-Inhalt in Datei speichern
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        save_utils_logger.info(f"Saved html to '{filepath}'")
        return True
    except Exception as e:
        save_utils_logger.error(
            f"Error while saving html to '{filename}' (folder='~/{folder}'):{e}"
        )
        return False


def generate_filename_from_url(url: str, extension: str = ".html") -> str:
    """Erstellt einen Dateinamen aus einer URL."""
    save_utils_logger.info(
        f"Generating filename from url '{url}' (extension='{extension}') ..."
    )
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        # Dateinamen bereinigen und Endung hinzufügen
        sanitized_filename = sanitize_filename(filename)
        resulting_filename = f"{sanitized_filename}{extension}"
        save_utils_logger.info(
            f"Generated filename from url '{url}' (extension='{extension}: '{resulting_filename}'')"
        )
        return resulting_filename
    except Exception as e:
        save_utils_logger.error(
            f"Error while generating filename from url '{url}' (extension='{extension}'):{e}"
        )
        return None
