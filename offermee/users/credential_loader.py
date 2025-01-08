import logging
from offermee.database.db_connection import connect_to_db
from offermee.database.models.user_model import UserModel


def load_credentials_from_db():
    """
    Lädt alle Benutzer aus der DB und gibt ein Dictionary zurück,
    das für streamlit_authenticator geeignet ist.

    Format:
    {
      "usernames": {
        "jsmith": {
          "name": "John Smith",
          "password": "$2b$12$...",
          "email": "john.smith@example.com"
        },
        ...
      }
    }
    """
    logger = logging.getLogger(__name__)
    session = connect_to_db()  # session factory aus db_connection
    credentials_dict = {"usernames": {}}

    try:
        users = session.query(UserModel).all()
        for user in users:
            # Wir setzen name, password, email
            # -> "password" muss der bcrypt-Hash sein
            credentials_dict["usernames"][user.username] = {
                "name": user.name,
                "password": user.password_hash,  # bereits gehashter String
                "email": user.email or "",
            }
    except Exception as e:
        logger.error(f"Fehler beim Laden der User aus der DB: {e}")
    finally:
        session.close()
    logger.info(f"Credentials aus DB geladen: {credentials_dict}")
    return credentials_dict
