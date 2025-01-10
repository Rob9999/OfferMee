# offermee/cv_exporter.py
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from offermee.database.db_connection import connect_to_db
from offermee.database.models.cv_model import CVModel


def export_cv_to_pdf(freelancer_id, language="de"):
    session = connect_to_db()
    cv = session.query(CVModel).filter_by(freelancer_id=freelancer_id).first()
    if not cv:
        return None

    pdf_filename = f"cv_{freelancer_id}_{language}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    data = json.loads(cv.structured_data)

    person = data.get("person", {}).get("person", {})
    # Introduction
    # Name
    firstnames = " ".join(person.get("firstnames", [""]))
    lastname = person.get("lastname", "")
    name_row = ""
    if firstnames and firstnames != "":
        name_row = f"Lebenslauf: {firstnames}"
    if lastname and lastname != "":
        name_row += f"{ lastname}"
    c.drawString(50, height - 50, name_row)
    # Birth
    birth = person.get("birth", "")
    birth_place = person.get("birth-place", "")
    if birth and birth != "":
        birth_row = f"Geboren am: {birth}"
        if birth_place and birth_place != "":
            birth_row += f" in {birth_place}"
        c.drawString(50, height - 70, birth_row)
    c.drawString(50, height - 90, f"Freelancer ID: {freelancer_id}")

    # Iteriere über Projekte und füge diese dem PDF hinzu
    projects = data.get("projects", [])
    y_position = height - 120
    for proj_entry in projects:
        project = proj_entry.get("project", {})
        c.drawString(
            50,
            y_position,
            f"Projekt: {project.get('title', '')} ({project.get('start', '')} - {project.get('end', '')})",
        )
        y_position -= 20
        # Füge weitere Details hinzu...
        if y_position < 100:
            c.showPage()  # neue Seite
            y_position = height - 50

    c.save()

    session.close()
    return pdf_filename
