from __future__ import annotations

from datetime import datetime
from io import BytesIO
from textwrap import wrap
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _items(items: list[str]) -> str:
    return "<br/>".join(f"- {item}" for item in items)


def _short(value: Any) -> str:
    text = str(value or "Not provided")
    return "<br/>".join(wrap(text, 85)) if len(text) > 90 else text


def generate_health_report_pdf(patient_data: dict[str, Any], result: Any, advice: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = []

    story.append(Paragraph("LifeLine AI Health Report", styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 10))

    summary = [
        ["Patient", _short(patient_data.get("patient_name") or "Anonymous")],
        ["Age / Gender", f"{patient_data.get('age', 'Not provided')} / {patient_data.get('gender', 'Not provided')}"],
        ["Symptoms", _short(", ".join(patient_data.get("symptoms", [])))],
        ["Existing conditions", _short(", ".join(patient_data.get("conditions", [])))],
        ["Medicines / allergies", _short(patient_data.get("medications"))],
        ["Risk level", result.risk_level],
        ["Risk score", f"{result.score}/100"],
        ["Likely pattern", result.possible_category],
        ["Recommended timeframe", advice["timeframe"]],
    ]
    table = Table(summary, colWidths=[1.8 * inch, 5.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E9F7F4")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#102420")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#7FBDB3")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BFDCD8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    sections = [
        ("Recommendation", result.recommendation),
        ("Why LifeLine AI thinks this", _items(result.signals)),
        ("What to do now", _items(advice["care_steps"])),
        ("Home care support", _items(advice["home_care"])),
        ("Precautions", _items(advice["precautions"])),
        ("What to avoid", _items(advice["avoid"])),
        ("Red flags", _items(advice["red_flags"])),
        ("Questions to ask a doctor", _items(advice["doctor_questions"])),
    ]
    for title, body in sections:
        story.append(Paragraph(f"<b>{title}</b>", styles["Heading3"]))
        story.append(Paragraph(str(body).replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Safety note</b>", styles["Heading3"]))
    story.append(
        Paragraph(
            "This report is general decision support. It does not diagnose, prescribe, or replace a doctor, pharmacist, or emergency service.",
            styles["BodyText"],
        )
    )
    doc.build(story)
    return buffer.getvalue()
