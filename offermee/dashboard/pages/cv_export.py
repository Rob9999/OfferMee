import os
import streamlit as st
from offermee.dashboard.widgets.selectors import render_cv_selection_form
from offermee.exporter.pdf_exporter import export_cv_to_pdf
from offermee.dashboard.international import _T
from offermee.dashboard.web_dashboard import log_error, log_info


def render():
    """
    Render the CV export page in the Streamlit dashboard.
    Allows users to select a CV, choose a language, and export it as a PDF.
    """
    st.header(_T("CV Export"))

    # Render the CV selection form
    render_cv_selection_form(_T("Select CV to export"))

    # Retrieve the selected CV from session state
    selected_cv_id = st.session_state.get("selected_cv_id")
    selected_cv = st.session_state.get("selected_cv")
    log_info(__name__, f"selected CV#{selected_cv_id}:\n{selected_cv}")
    if selected_cv_id:
        log_info(__name__, f"Selected CV#{selected_cv_id} to export to pdf.")
        # Language selection for export
        language = st.selectbox(
            _T("Select export language:"), options=["de", "en", "fr", "es"]
        )

        # Button to trigger PDF export
        if st.button(_T("Export CV as PDF")):
            try:
                # Export the selected CV to a PDF file
                pdf_filename = export_cv_to_pdf(selected_cv, language=language)

                if pdf_filename and os.path.exists(pdf_filename):
                    st.success(
                        _T("CV was successfully exported: {}").format(pdf_filename)
                    )

                    # Offer the PDF file for download
                    with open(pdf_filename, "rb") as pdf_file:
                        st.download_button(
                            label=_T("Download PDF"),
                            data=pdf_file,
                            file_name=os.path.basename(pdf_filename),
                            mime="application/pdf",
                        )
                else:
                    st.error(_T("An error occurred while exporting the CV."))
            except Exception as e:
                # Log the error and display an error message
                log_error("Error during CV export: {}", str(e))
                st.error(_T("An unexpected error occurred. Please try again."))
