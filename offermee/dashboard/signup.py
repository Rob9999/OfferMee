import streamlit as st
from offermee.users.user_management import register_user


def signup_render():
    st.title("Sign up")

    username = st.text_input("Username")
    email = st.text_input("Email (optional)")
    password = st.text_input("Passwort", type="password")
    if st.button("Jetzt registrieren"):
        ok, msg = register_user(username, password, email)
        if ok:
            st.success(msg)
        else:
            st.error(msg)
