import streamlit as st


def render():
    st.header("CV hinterlegen")
    cv = st.text_area("Fügen Sie Ihren Lebenslauf ein:")
    if st.button("Speichern"):
        st.success("CV erfolgreich gespeichert!")
