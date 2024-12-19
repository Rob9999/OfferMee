import streamlit as st


def render():
    st.header("Projektübersicht")
    st.write("Hier werden die Projekte angezeigt, die mit Ihrem CV übereinstimmen.")
    if st.button("Angebot erstellen"):
        st.success("Angebot erfolgreich erstellt!")
