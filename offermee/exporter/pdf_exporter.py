import os
import traceback
from typing import Any, Dict, List, Optional, Union
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from offermee.utils.config import Config
from offermee.utils.logger import CentralLogger


pdf_exporter_logger = CentralLogger.getLogger(__name__)


def export_cv_to_pdf(name: str, cv_data: Dict[str, Any], language: str = "de") -> str:
    """
    Exports a CV to a PDF file.
    Args:
        name (str): The name of the person whose CV is being exported.
        cv_data (Dict[str, Any]): The CV data containing personal information, education, skills, projects, jobs, and contact details.
        language (str, optional): The language of the CV. Defaults to "de".
    Returns:
        str: The file path of the generated PDF if successful, otherwise None.
    Raises:
        ValueError: If the CV data is corrupted or missing required fields.
    """
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
        Config.get_instance().get_user_temp_dir(), f"CV_{name}_{language}.pdf"
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
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
        styles = getSampleStyleSheet()
        paragraph_style = ParagraphStyle(
            name="Wrapped",
            fontName="DejaVu",  # Use our TrueType font
            fontSize=10,
            leading=12,
            wordWrap="CJK",
        )
        elements = []

        management_summary = cv_data.get("management-summary")
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
            elements.append(Paragraph("<b>Personal Data</b>", styles["Heading2"]))
            elements.append(Spacer(1, 0.2 * inch))
            headers = [
                "Name:",
                f"{' '.join(person.get('firstnames', ['']))} {person.get('lastname', '')}",
            ]
            personal_info = [
                ["Date of Birth:", person.get("birth", "")],
                ["Place of Birth:", person.get("birth-place", "")],
                [
                    "Address:",
                    f"{person.get('address', '')}, {person.get('zip-code', '')} {person.get('city', '')}, {person.get('country', '')}",
                ],
                ["Phone:", person.get("phone", "")],
                ["Email:", person.get("email", "")],
                ["LinkedIn:", person.get("linkedin", "")],
                ["Xing:", person.get("xing", "")],
                ["Github:", person.get("github", "")],
                ["Website:", person.get("website", "")],
                ["Languages:", ", ".join(person.get("languages", []))],
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
                headers=headers,
                data=personal_info,
                style_commands=table_style,
                paragraph_style=paragraph_style,
            )
            if table:
                elements.append(table)
                elements.append(Spacer(1, 0.5 * inch))

        # Education
        if educations:
            elements.append(Paragraph("<b>Education</b>", styles["Heading2"]))
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
                    "Person Days",
                    edu.get("person-days"),
                    styles["Normal"],
                )
                _util_add_valid_paragraph(
                    elements, "Institution", edu.get("facility"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements, "Type", edu.get("type"), styles["Normal"]
                )
                _util_add_valid_paragraph(
                    elements, "Degree", edu.get("grade"), styles["Normal"]
                )
                topics = edu.get("topics", [])
                if topics:
                    _util_add_valid_paragraph_list(
                        elements, "", topics, styles["Normal"], styles["Bullet"]
                    )
                elements.append(Spacer(1, 0.2 * inch))

        # Skills
        metrics: List[Dict[str, Any]] = cv_data.get("metrics", [])
        if metrics:
            # build metrics tables according to schema
            to_table = True
            if to_table:
                for metric in metrics:
                    metric_entry = metric.get("metric", {})
                    metric_category = metric_entry.get("category")
                    metric_type = metric_entry.get("type")
                    metric_details: List[Dict[str, Any]] = metric_entry.get(
                        "details", []
                    )
                    if not metric_category or not metric_details:
                        continue

                    # Heading
                    elements.append(
                        Paragraph(f"<b>{metric_category}</b>", styles["Heading2"])
                    )
                    elements.append(Spacer(1, 0.2 * inch))

                    # Collect data for the table
                    metric_headers = ["Skill", "Level", "Months", "Description"]
                    metric_info = []
                    for detail in metric_details:
                        skill = detail.get("skill")
                        level = detail.get("level")
                        month = detail.get("month")
                        description = detail.get("description")

                        # Skip row if skill is empty
                        if not skill:
                            continue

                        metric_info.append([skill, level, month, description])

                    # Table styles:
                    #   - Entire table left-aligned
                    #   - Erste Zeile fett (falls du Headings separat hast, müsstest du sie in `metric_info` einschleusen)
                    #   - Linierung und Abstände nach Bedarf
                    table_style = [
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ]

                    # Tabelle erzeugen
                    table = _create_flexible_table(
                        headers=metric_headers,
                        data=metric_info,
                        style_commands=table_style,
                        paragraph_style=paragraph_style,
                    )

                    if table:
                        elements.append(table)
                        elements.append(Spacer(1, 0.5 * inch))
            else:
                for metric in metrics:
                    # print(metric)
                    metric_entry = metric.get("metric", {})
                    metric_category = metric_entry.get("category")
                    metric_details: List[Dict[str, Any]] = metric_entry.get(
                        "details", []
                    )
                    if not metric_category or not metric_details:
                        continue

                elements.append(
                    Paragraph(f"<b>{metric_category}</b>", styles["Heading2"])
                )
                elements.append(Spacer(1, 0.2 * inch))
                # print(metric)
                for detail in metric_details:
                    skill = detail.get("skill")
                    level = detail.get("level")
                    month = detail.get("month")
                    description = detail.get("description")
                    print(skill, level, month, description)
                    # if not skill or not level or not month:
                    #    continue
                    elements.append(Paragraph(f"<b>{skill}</b>", styles["Heading3"]))
                    _util_add_valid_paragraph(
                        elements, "Level", level, styles["Normal"]
                    )
                    _util_add_valid_paragraph(
                        elements, "Monate", month, styles["Normal"]
                    )
                    _util_add_valid_paragraph(
                        elements, "Beschreibung", description, styles["Normal"]
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


def remove_empty_columns(
    headers: List[Any], data: List[List[Any]]
) -> tuple[List[Any], List[List[Any]]]:
    """
    Removes columns that are completely empty (no values).
    'Empty' here means None, empty string, empty list, or value 0.
    """
    if not data:
        return data

    # Find the maximum number of columns in the rows
    max_cols = max(len(row) for row in data)

    # Determine which columns to keep
    columns_to_keep = []
    for col_index in range(max_cols):
        # If there is something in this column in *any* row, we keep it
        # (provided the row is long enough).
        keep_this_col = any(
            len(row) > col_index and row[col_index] not in (None, "", [], 0, 0.0)
            for row in data
        )
        if keep_this_col:
            columns_to_keep.append(col_index)

    # New data structure with only the columns to keep
    new_data = []
    for row in data:
        new_row = [row[i] for i in columns_to_keep if i < len(row)]
        new_data.append(new_row)
    if headers:
        new_headers = [headers[i] for i in columns_to_keep if i < len(headers)]
        return new_headers, new_data
    return None, new_data


def measure_column_widths(data: List[List[Any]]) -> List[int]:
    if not data:
        return []
    max_cols = max(len(row) for row in data)
    column_widths = [0] * max_cols
    header = True
    for row in data:
        for col_index, cell in enumerate(row):
            if isinstance(cell, Paragraph):
                text = cell.text
                column_widths[col_index] = max(column_widths[col_index], len(text))
            elif cell is not None and cell != "" and cell != []:
                column_widths[col_index] = max(column_widths[col_index], len(str(cell)))
            if header:
                column_widths[col_index] += 5
        if header:
            header = False
    return column_widths


def measure_column_widths_normalized(data: List[List[Any]]) -> List[float]:
    col_widths = measure_column_widths(data=data)
    col_width_sum = sum(col_widths)
    col_widths_normalized = [
        col_width_normalized * 100 / col_width_sum
        for col_width_normalized in col_widths
    ]
    return col_widths_normalized


def adjust_column_widths(
    column_widths: List[int],
    normalized_column_widths: List[float],
    available_width: float,
) -> List[int]:
    if not column_widths:
        return []
    if not normalized_column_widths:
        return column_widths
    if not available_width:
        return column_widths
    for i in range(len(column_widths)):
        column_widths[i] = normalized_column_widths[i] * available_width / 100
    return column_widths


def _create_flexible_table(
    headers: List[str],
    data: List[List[Any]],
    style_commands: List[Any],
    paragraph_style: ParagraphStyle,
) -> Table:
    """
    Creates a table from 'cv_data'.
    Removes empty rows and columns.
    """
    # 1. Filter empty rows (second element empty, etc. – adjust if more columns).
    #    If you want to check ALL columns, you would need to check each column instead of row[1].
    filtered_rows = [
        row for row in data if any(cell not in [None, "", [], 0, 0.0] for cell in row)
    ]
    if not filtered_rows:
        return None

    # 2. Filter columns
    filtered_headers, filtered_data = remove_empty_columns(
        headers=headers, data=filtered_rows
    )
    if not filtered_data:
        return None

    if filtered_headers:
        filtered_data.insert(0, filtered_headers)

    # 2.1. Calculate column widths
    col_text_widths_normalized = measure_column_widths_normalized(
        [filtered_headers] + filtered_data
    )

    # 3. UTF-32 conversion (optional)
    # for row_index, row in enumerate(filtered_data):
    #    for col_index in range(len(row)):
    #        filtered_data[row_index][col_index] = row[col_index]

    # 4. Convert to Paragraphs + Unicode-capable font
    #    This allows ReportLab to handle layout (wrapping) automatically.
    for row_index, row in enumerate(filtered_data):
        for col_index, cell_value in enumerate(row):
            if cell_value is None:
                cell_value = ""
            # Important: with Paragraph, ReportLab can control the layout (wrapping)
            filtered_data[row_index][col_index] = Paragraph(
                str(cell_value), paragraph_style
            )

    # 4. Calculate table width (e.g., DIN A4, minus 2 * 1 inch margin => "available_width")
    #    You can also use doc.width if you have a SimpleDocTemplate(...).
    PAGE_WIDTH, PAGE_HEIGHT = A4
    left_margin = right_margin = inch
    available_width = PAGE_WIDTH - left_margin - right_margin

    # 5. Finally calculate column widths
    col_widths = measure_column_widths([filtered_headers] + filtered_data)
    # 3.1 Adjust column widths according to the normalized text widths
    col_widths = adjust_column_widths(
        column_widths=col_widths,
        normalized_column_widths=col_text_widths_normalized,
        available_width=available_width,
    )
    print(col_widths)

    # 4. Create table
    table = Table(filtered_data, colWidths=col_widths)
    table.setStyle(TableStyle(style_commands))
    return table
