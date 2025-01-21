import os
import traceback
from typing import Any, Dict, List, Optional, Union
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from offermee.config import Config
from offermee.logger import CentralLogger


pdf_exporter_logger = CentralLogger.getLogger(__name__)


def export_cv_to_pdf(name: str, cv_data: Dict[str, Any], language: str = "de") -> str:
    if not name:
        pdf_exporter_logger.error(
            f"Argument Error: name:'{name}'. Unable to export cv to pdf."
        )
        return None
    if not cv_data:
        pdf_exporter_logger.error(
            f"Argument Error: cv_data:'{cv_data}'. Unable to export cv to pdf."
        )
        return None
    pdf_filename = os.path.join(
        Config.get_instance().get_user_temp_dir(), f"cv_{name}_{language}.pdf"
    )
    try:
        pdf_exporter_logger.info(f"Exporting CV '{pdf_filename}' ...")
        person: Dict[str, Any] = cv_data.get("person", {})
        if not person:
            raise ValueError("data corrupted: no 'person'")
        firstnames = person.get("firstnames")
        if not firstnames:
            raise ValueError("data corrupted: no 'firstnames'")
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        management_summary = None
        educations: List[Dict[str, Any]] = cv_data.get("educations")
        projects: List[Dict[str, Any]] = cv_data.get("projects")
        jobs: List[Dict[str, Any]] = cv_data.get("jobs")
        contacts: List[Dict[str, Any]] = cv_data.get("contacts", [])
        contact: Optional[Dict[str, Any]] = contacts[0] if contacts else None
        contact: Optional[Dict[str, Any]] = (
            contact.get("contact") if contact and contact.get("contact") else None
        )

        # Management Summary
        if management_summary:
            elements.append(Paragraph("<b>Management Summary</b>", styles["Title"]))
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph(management_summary, styles["Normal"]))
            elements.append(Spacer(1, 0.5 * inch))

        # Personal cv_data
        if person:
            elements.append(Paragraph("<b>Persönliche Daten</b>", styles["Heading2"]))
            elements.append(Spacer(1, 0.2 * inch))
            personal_info = [
                [
                    "Name:",
                    f"{' '.join(person.get('firstnames', ['']))} {person.get('lastname', '')}",
                ],
                ["Geburtsdatum:", person.get("birth", "")],
                ["Geburtsort:", person.get("birth-place", "")],
                [
                    "Adresse:",
                    f"{person.get('address', '')}, {person.get('zip-code', '')} {person.get('city', '')}, {person.get('country', '')}",
                ],
                ["Telefon:", person.get("phone", "")],
                ["E-Mail:", person.get("email", "")],
                ["LinkedIn:", person.get("linkedin", "")],
                ["Xing:", person.get("xing", "")],
                ["Github:", person.get("github", "")],
                ["Website:", person.get("website", "")],
                ["Sprachen:", ", ".join(person.get("languages", []))],
            ]
            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
            table = _create_flexible_table(
                personal_info, [2 * inch, 4.1 * inch], table_style
            )
            if table:
                elements.append(table)
                elements.append(Spacer(1, 0.5 * inch))

        # Education
        if educations:
            elements.append(Paragraph("<b>Ausbildung</b>", styles["Heading2"]))
            elements.append(Spacer(1, 0.2 * inch))
            for education in educations:
                edu = education.get("education", {})
                elements.append(
                    Paragraph(
                        f"<b>{edu.get('title', '')}</b> {_util_get_valid_from_til_str(edu.get('start', ''), edu.get('end', ''))}",
                        styles["Heading3"],
                    )
                )
                _util_add_valid_paragraph(
                    elements,
                    "Personentage",
                    edu.get("person-days"),
                    styles["Normal"],
                )
                _util_add_valid_paragraph(
                    elements, "Einrichtung", edu.get("facility"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements, "Art", edu.get("type"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements, "Abschluss", edu.get("grade"), styles["Normal"]
                )
                topics = edu.get("topics", [])
                if topics:
                    _util_add_valid_paragraph_list(
                        elements, "Themen", topics, styles["Normal"], styles["Bullet"]
                    )
                elements.append(Spacer(1, 0.2 * inch))

        # Projects
        if projects:
            elements.append(Paragraph("<b>Projekterfahrungen</b>", styles["Heading2"]))
            elements.append(Spacer(1, 0.2 * inch))
            for proj_entry in projects:
                project = proj_entry.get("project", {})
                elements.append(
                    Paragraph(
                        f"<b>{project.get('title', '')}</b> ({project.get('start', '')} - {project.get('end', '')})",
                        styles["Heading3"],
                    )
                )
                _util_add_valid_paragraph(
                    elements, f"Ergebnis", project.get("result"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements,
                    "Personentage",
                    project.get("person-days"),
                    styles["Normal"],
                )
                _util_add_valid_paragraph(
                    elements, "Branche", project.get("industry"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements, "Firma", project.get("firm"), styles["Normal"]
                )
                _util_add_valid_paragraph_list(
                    elements,
                    "Aufgaben",
                    project.get("tasks", []),
                    styles["Normal"],
                    styles["Bullet"],
                )
                tech_skills = project.get("tech-skills", [])
                if tech_skills:
                    elements.append(
                        Paragraph(
                            f"Technologien: {', '.join(tech_skills)}", styles["Normal"]
                        )
                    )
                soft_skills = project.get("soft-skills", [])
                if soft_skills:
                    elements.append(
                        Paragraph(
                            f"Soft-Skills: {', '.join(soft_skills)}", styles["Normal"]
                        )
                    )
                responsibilities = project.get("responsibilities", [])
                if responsibilities:
                    _util_add_valid_paragraph_list(
                        elements,
                        "Verantwortlichkeiten",
                        responsibilities,
                        styles["Normal"],
                        styles["Bullet"],
                    )
                elements.append(Spacer(1, 0.2 * inch))

        # Jobs
        if jobs:
            elements.append(
                Paragraph("<b>Berufserfahrungen / Anstellungen</b>", styles["Heading2"])
            )
            elements.append(Spacer(1, 0.2 * inch))
            for job_entry in jobs:
                job = job_entry.get("job", {})
                elements.append(
                    Paragraph(
                        f"<b>{job.get('title', '')}</b> ({job.get('start', '')} - {job.get('end', '')})",
                        styles["Heading3"],
                    )
                )
                _util_add_valid_paragraph(
                    elements, f"Ergebnis", job.get("result"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements,
                    "Personentage",
                    job.get("person-days"),
                    styles["Normal"],
                )
                _util_add_valid_paragraph(
                    elements, "Branche", job.get("industry"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements, "Firma", job.get("firm"), styles["Normal"]
                )
                _util_add_valid_paragraph_list(
                    elements,
                    "Aufgaben",
                    job.get("tasks", []),
                    styles["Normal"],
                    styles["Bullet"],
                )
                tech_skills = job.get("tech-skills", [])
                if tech_skills:
                    elements.append(
                        Paragraph(
                            f"Technologien: {', '.join(tech_skills)}", styles["Normal"]
                        )
                    )
                soft_skills = job.get("soft-skills", [])
                if soft_skills:
                    elements.append(
                        Paragraph(
                            f"Soft-Skills: {', '.join(soft_skills)}", styles["Normal"]
                        )
                    )
                responsibilities = job.get("responsibilities", [])
                if responsibilities:
                    _util_add_valid_paragraph_list(
                        elements,
                        "Verantwortlichkeiten",
                        responsibilities,
                        styles["Normal"],
                        styles["Bullet"],
                    )
                elements.append(Spacer(1, 0.2 * inch))

        # Contact
        if contact:
            elements.append(Paragraph("<b>Kontakt</b>", styles["Heading2"]))
            elements.append(Spacer(1, 0.2 * inch))
            _util_add_valid_paragraph(
                elements, "Adresse", contact.get("address"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "Stadt", contact.get("city"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "PLZ", contact.get("zip-code"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "Land", contact.get("country"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "Telefon", contact.get("phone"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "E-Mail", contact.get("email"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "LinkedIn", contact.get("linkedin"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "Xing", contact.get("xing"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "Github", contact.get("github"), styles["Normal"]
            )
            _util_add_valid_paragraph(
                elements, "Web", contact.get("website"), styles["Normal"]
            )
            elements.append(Spacer(1, 0.2 * inch))

        # Save PDF
        try:
            doc.build(elements)
            pdf_exporter_logger.info(f"Successfully created PDF: {pdf_filename}")
        except Exception as e:
            pdf_exporter_logger.error(f"Failed to generate PDF for '{name}': {e}")
            return None

        return pdf_filename
    except Exception as e:
        pdf_exporter_logger.error(
            f"Unable to export CV to PDF. CV data may be corrupted : {e}"
        )
        traceback.print_exception(type(e), e, e.__traceback__)
        return None


def _util_get_valid_from_til_str(start: str, end: str):
    if not start and not end:
        return ""
    return f"({start} - {end})" if start or end else ""


def _util_add_valid_paragraph(
    elements: list, label: str, content: Union[str, int], style
):
    if not elements or not isinstance(elements, list):
        return
    if not content or content == "" or content is None:
        return
    if not label or label == "" or label is None:
        elements.append(Paragraph(f"{content}", style))
    else:
        elements.append(Paragraph(f"{label}: {content}", style))


def _util_add_valid_paragraph_list(
    elements: list, label: str, items: list, label_style, bullet_style
):
    if not elements or not isinstance(elements, list):
        return
    if not items:
        return
    if label:
        elements.append(Paragraph(f"{label}:", label_style))
    for item in items:
        elements.append(Paragraph(f"{item}", bullet_style))


def _create_flexible_table(cv_data: list, col_widths, style_commands):
    """
    Erstellt eine Tabelle aus 'cv_data', wobei Zeilen mit leeren oder null Inhalten ausgeschlossen werden.
    :param cv_data: Liste von Zeilen, wobei jede Zeile eine Liste [Label, Inhalt] ist.
    :param col_widths: Spaltenbreiten für die Tabelle.
    :param style_commands: Stilbefehle für die Tabelle.
    :return: reportlab.platypus.Table-Objekt oder None, falls keine gültigen Zeilen vorhanden sind.
    """
    # Filtere Zeilen, bei denen der Inhalt leer oder None ist
    filtered_data = [row for row in cv_data if row[1] not in [None, "", []]]
    if not filtered_data:
        return None

    table = Table(filtered_data, colWidths=col_widths)
    table.setStyle(TableStyle(style_commands))
    return table
