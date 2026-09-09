import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


def generate_pdf_report(result: dict) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("BidGuard AI - Bid Compliance Report", styles["Title"]))
    story.append(Spacer(1, 12))

    tender = result.get("tender", {}).get("tender_summary", {})
    score = result.get("score", {})

    story.append(Paragraph(
        f"<b>Tender:</b> {tender.get('title', 'N/A')}",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        f"<b>Organisation:</b> {tender.get('organisation', 'N/A')}",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        f"<b>Tender ID:</b> {tender.get('tender_id', 'N/A')}",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        f"<b>Compliance Score:</b> {score.get('score', 0)}%",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        f"<b>Recommendation:</b> {score.get('recommendation', 'N/A')}",
        styles["BodyText"],
    ))

    story.append(Spacer(1, 16))

    data = [["Requirement", "Status", "Risk", "Confidence"]]

    for row in result.get("compliance", {}).get("compliance_results", []):
        data.append([
            row.get("requirement", "")[:70],
            row.get("status", ""),
            row.get("risk", ""),
            f'{row.get("confidence", 0)}%',
        ])

    table = Table(data, repeatRows=1, colWidths=[260, 80, 70, 70])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(table)
    story.append(Spacer(1, 16))

    recommendation = result.get("recommendation", "")
    story.append(Paragraph("<b>AI Recommendation</b>", styles["Heading2"]))
    for paragraph in recommendation.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles["BodyText"]))
            story.append(Spacer(1, 5))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Disclaimer: This report is an AI-assisted assessment. "
        "Verify all decisions against the original tender and applicable rules.",
        styles["BodyText"],
    ))

    doc.build(story)
    return buffer.getvalue()
