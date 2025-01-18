import os
import subprocess
import logging
import polib

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pybabel_script")

# Languages
supported_languages = {
    "de": {"locale": "de_DE"},
    "en": {"locale": "en_US"},
}
# update (:=False --> automatic translation and integrating new languages)
update = False

# Directories and files
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCALES_DIR = os.path.join(BASE_DIR, "locales")
BABEL_CFG = os.path.join(BASE_DIR, "babel.cfg")
POT_FILE = os.path.join(LOCALES_DIR, "messages.pot")
DOMAIN = "messages"
DEFAULT_LANGUAGE = "de"

# Ensure the locales directory exists
if not os.path.exists(LOCALES_DIR):
    os.makedirs(LOCALES_DIR)
    logger.info(f"Created locales directory at {LOCALES_DIR}")


# Translation method using polib to fill msgstr with msgid
def hypothetical_translate(language, po_file_path):
    logger.info(f"Filling translations for language '{language}' in {po_file_path}.")
    try:
        # Load PO-File
        po = polib.pofile(po_file_path)
        # translate each msgid entry and set to msgstr if msgstr empty
        for entry in po:
            if not entry.msgstr:
                entry.msgstr = entry.msgid  # TODO translate
        # Save translated PO-File
        po.save()
        logger.info(f"Translations for language '{language}' updated successfully.")
    except Exception as e:
        logger.error(f"Error during hypothetical translation for {language}: {e}")


try:
    # Step 4: Extract messages into a POT file
    logger.info("Extracting messages into POT file...")
    subprocess.run(
        [
            "pybabel",
            "extract",
            "-F",
            BABEL_CFG,
            "-k",
            "_T gettext ngettext lazy_gettext",
            "-o",
            POT_FILE,
            BASE_DIR,
        ],
        check=True,
    )
    logger.info("Extraction successful.")

    if not update:
        # Step 5 und 6: Initialize and translate for each supported language
        for lang_code, lang_info in supported_languages.items():
            logger.info(f"Initializing new language catalog for {lang_code}...")
            subprocess.run(
                ["pybabel", "init", "-i", POT_FILE, "-d", LOCALES_DIR, "-l", lang_code],
                check=True,
            )
            logger.info(f"Initialization of {lang_code} successful.")

            # Pfad zur erzeugten PO-Datei
            po_file = os.path.join(
                LOCALES_DIR, lang_code, "LC_MESSAGES", f"{DOMAIN}.po"
            )
            logger.info(
                f"Starting hypothetical translation for {lang_code} into {po_file}"
            )
            hypothetical_translate(lang_code, po_file)
    else:
        # Update existing catalogs
        subprocess.run(
            ["pybabel", "update", "-i", POT_FILE, "-d", LOCALES_DIR], check=True
        )
        logger.info("Update successful.")

    # Step 8: Compile the translations
    logger.info("Compiling translations...")
    subprocess.run(["pybabel", "compile", "-d", LOCALES_DIR], check=True)
    logger.info("Compilation successful.")

except subprocess.CalledProcessError as e:
    logger.error(f"An error occurred: {e}")
