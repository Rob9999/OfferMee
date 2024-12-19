import streamlit as st


def render():
    st.header("Standardangebotstemplate")
    template = st.text_area("Geben Sie Ihr Angebotstemplate ein:")
    if st.button("Speichern"):
        st.success("Template erfolgreich gespeichert!")
