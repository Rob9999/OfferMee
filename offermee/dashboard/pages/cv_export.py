# offermee/dashboard/pages/export_cv.py
import os
import streamlit as st
from offermee.database.db_connection import connect_to_db
from offermee.database.models.cv_model import CVModel
from offermee.exporter.pdf_exporter import export_cv_to_pdf


def render():
    st.header("CV Export")

    # Verbindung zur Datenbank herstellen
    session = connect_to_db()

    # Alle verfügbaren CV-Einträge abrufen
    cvs = session.query(CVModel).all()

    if not cvs:
        st.info("Keine Lebensläufe in der Datenbank gefunden.")
        session.close()
        return

    # Übersichtstabelle der verfügbaren CVs
    cv_table_data = []
    for cv in cvs:
        # Hier können weitere Freelancer-Informationen eingebunden werden
        cv_table_data.append(
            {
                "CV-ID": cv.id,
                "Freelancer-ID": cv.freelancer_id,
                "Letztes Update": (
                    cv.structured_data[:50] + "..." if cv.structured_data else ""
                ),
            }
        )

    # Anzeige der Tabelle
    st.subheader("Verfügbare Lebensläufe")
    selected_cv_id = st.selectbox(
        "Wählen Sie einen CV zum Exportieren aus:",
        options=[cv["CV-ID"] for cv in cv_table_data],
        format_func=lambda x: f"CV {x} (Freelancer {next(item['Freelancer-ID'] for item in cv_table_data if item['CV-ID'] == x)})",
    )

    # Sprachwahl für den Export (optional)
    language = st.selectbox("Sprache für den Export:", options=["de", "en", "fr", "es"])

    # Knopf zum Exportieren
    if st.button("CV als PDF exportieren"):
        # Finde das ausgewählte CV-Modell
        selected_cv = session.query(CVModel).filter_by(id=selected_cv_id).first()
        if not selected_cv:
            st.error("Gewählter Lebenslauf nicht gefunden.")
        else:
            # Exportiere den CV als PDF
            pdf_filename = export_cv_to_pdf(selected_cv, language=language)
            if pdf_filename and os.path.exists(pdf_filename):
                st.success(f"Lebenslauf wurde erfolgreich exportiert: {pdf_filename}")
                # Biete dem Nutzer an, die PDF-Datei herunterzuladen
                with open(pdf_filename, "rb") as pdf_file:
                    st.download_button(
                        label="PDF herunterladen",
                        data=pdf_file,
                        file_name=os.path.basename(pdf_filename),
                        mime="application/pdf",
                    )
            else:
                st.error("Fehler beim Exportieren des Lebenslaufs.")

    session.close()
