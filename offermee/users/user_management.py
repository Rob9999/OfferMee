import bcrypt
from offermee.database.db_connection import connect_to_db
from offermee.database.models.user_model import UserModel


def register_user(username, password, role="user", name=None, email=None):
    session = connect_to_db()
    try:
        # Prüfen ob username schon existiert
        existing = session.query(UserModel).filter_by(username=username).first()
        if existing:
            return False, "Username existiert bereits."

        # Passwort hashen (bcrypt)
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

        new_user = UserModel(
            username=username,
            password_hash=password_hash.decode("utf-8"),
            role=role,
            name=name is None and username or name,
            email=email,
        )
        session.add(new_user)
        session.commit()
        return True, "User erfolgreich registriert."
    except Exception as e:
        session.rollback()
        return False, f"Fehler: {e}"
    finally:
        session.close()


def login_user(username, password):
    session = connect_to_db()
    try:
        user = session.query(UserModel).filter_by(username=username).first()
        if not user:
            return False, "User nicht gefunden."

        # bcrypt.checkpw gibt True/False zurück
        if bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            return True, "Login erfolgreich."
        else:
            return False, "Falsches Passwort."
    except Exception as e:
        return False, f"Fehler: {e}"
    finally:
        session.close()
