# offermee/dashboard/pages/export_cv.py
import os
from typing import Any, Dict, List
import streamlit as st
from offermee.database.db_connection import connect_to_db
from offermee.database.facades.main_facades import CVFacade
from offermee.exporter.pdf_exporter import export_cv_to_pdf


def render():
    st.header("CV Export")

    # Alle verfügbaren CV-Einträge abrufen
    cvs: List[Dict[str, Any]] = CVFacade.get_all()

    if not cvs:
        st.info("Keine Lebensläufe in der Datenbank gefunden.")
        return

    # Übersichtstabelle der verfügbaren CVs
    cv_table_data = []
    for cv in cvs:
        # Hier können weitere Freelancer-Informationen eingebunden werden
        cv_table_data.append(
            {
                "CV-ID": cv.get("id"),
                "Freelancer-ID": cv.get("freelancer_id"),
                "Name": cv.get("name"),
                "Letztes Update": (
                    cv.get("structured_data", [])[:50] + "..."
                    if cv.get("structured_data")
                    else "<LEER>"
                ),
            }
        )

    # Anzeige der Tabelle
    st.subheader("Verfügbare Lebensläufe")
    selected_cv_id = st.selectbox(
        "Wählen Sie einen CV zum Exportieren aus:",
        options=[cv["CV-ID"] for cv in cv_table_data],
        format_func=lambda x: f"CV {x}, Freelancer #{next(item['Freelancer-ID'] for item in cv_table_data if item['CV-ID'] == x)} {next(item['Name'] for item in cv_table_data if item['CV-ID'] == x)}",
    )

    # Sprachwahl für den Export (optional)
    language = st.selectbox("Sprache für den Export:", options=["de", "en", "fr", "es"])

    # Knopf zum Exportieren
    if st.button("CV als PDF exportieren"):
        # Finde das ausgewählte CV-Modell
        selected_cv: Dict[str, Any] = CVFacade.get_by_id(id=selected_cv_id)
        if not selected_cv:
            st.error("Gewählter Lebenslauf nicht gefunden.")
        else:
            # Exportiere den CV als PDF
            pdf_filename = export_cv_to_pdf(
                selected_cv.get("freelancer_id"), language=language
            )
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
