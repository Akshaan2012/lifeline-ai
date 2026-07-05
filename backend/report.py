from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _items(items: list[str]) -> str:
    return "<br/>".join(f"- {item}" for item in items)


def _short(value: Any) -> str:
    text = str(value or "Not provided")
    return text


def _p(text: Any, style: Any) -> Paragraph:
    return Paragraph(escape(str(text)), style)


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

    symptoms_text = _short(", ".join(patient_data.get("symptoms", [])))
    summary = [
        [_p("Patient", styles["BodyText"]), _p(_short(patient_data.get("patient_name") or "Anonymous"), styles["BodyText"])],
        [_p("Age / Gender", styles["BodyText"]), _p(f"{patient_data.get('age', 'Not provided')} / {patient_data.get('gender', 'Not provided')}", styles["BodyText"])],
        [_p("Symptoms", styles["BodyText"]), ""],
        [_p(symptoms_text, styles["BodyText"]), ""],
        [_p("Existing conditions", styles["BodyText"]), _p(_short(", ".join(patient_data.get("conditions", []))), styles["BodyText"])],
        [_p("Current medicines", styles["BodyText"]), _p(_short(patient_data.get("medications")), styles["BodyText"])],
        [_p("Allergies", styles["BodyText"]), _p(_short(patient_data.get("allergies")), styles["BodyText"])],
        [_p("Risk level", styles["BodyText"]), _p(result.risk_level, styles["BodyText"])],
        [_p("Risk score", styles["BodyText"]), _p(f"{result.score}/100", styles["BodyText"])],
        [_p("Likely pattern", styles["BodyText"]), _p(result.possible_category, styles["BodyText"])],
        [_p("Recommended timeframe", styles["BodyText"]), _p(advice["timeframe"], styles["BodyText"])],
    ]
    table = Table(summary, colWidths=[1.8 * inch, 4.65 * inch])
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
                ("SPAN", (0, 2), (1, 2)),
                ("SPAN", (0, 3), (1, 3)),
                ("BACKGROUND", (0, 2), (1, 2), colors.HexColor("#E9F7F4")),
                ("BACKGROUND", (0, 3), (1, 3), colors.white),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    sections = [
        ("AI-assisted patient overview" if advice.get("source") else "Patient overview", advice["report_summary"]),
        ("Doctor handoff", advice["doctor_handoff"]),
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
    if advice.get("source"):
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                "The overview and doctor handoff were written with OpenAI and constrained by LifeLine AI safety rules.",
                styles["BodyText"],
            )
        )
    doc.build(story)
    return buffer.getvalue()
