import streamlit as st
import streamlit_authenticator as stauth

from offermee.users.credential_loader import load_credentials_from_db


def main():
    st.title("Login Demo mit Streamlit-Authenticator + DB")

    # 1) Aktuelle Credentials laden:
    credentials = load_credentials_from_db()

    # 2) Authenticator anlegen
    authenticator = stauth.Authenticate(
        credentials,  # dict aus der DB
        "my_cookie_name",  # Cookie Name
        "my_random_salt_value",  # Irgendein geheimer/random String
        cookie_expiry_days=7,
    )

    # 3) Login-Widget anzeigen
    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status == False:
        st.error("Benutzername oder Passwort ist falsch.")
    elif authentication_status == None:
        st.warning("Bitte die Felder ausfüllen.")
    else:
        st.success(f"Willkommen, {name}!")
        st.write("Du bist eingeloggt. Hier könnte geschützter Inhalt stehen.")
        if st.button("Logout"):
            authenticator.logout("Logout", "main")
            st.rerun()


if __name__ == "__main__":
    main()
