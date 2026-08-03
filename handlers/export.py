import csv
import io
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

import database as db
from roles import require_role

router = Router()


def _all_incidents_rows():
    """Fetch every incident with resolved reporter/assignee names, newest first."""
    incidents = db.list_incidents()
    rows = []
    for inc in incidents:
        reporter = db.get_user_by_id(inc["reporter_id"])
        assignee = db.get_user_by_id(inc["assigned_to"]) if inc["assigned_to"] else None
        rows.append({
            "id": inc["id"],
            "title": inc["title"],
            "category": inc["category"],
            "severity": inc["severity"],
            "status": inc["status"],
            "reporter": reporter["username"] if reporter else "unknown",
            "assignee": assignee["username"] if assignee else "unassigned",
            "created_at": inc["created_at"],
            "updated_at": inc["updated_at"],
            "description": inc["description"],
        })
    return rows


@router.callback_query(F.data == "export:csv")
@require_role("viewer")
async def export_csv(callback: CallbackQuery):
    rows = _all_incidents_rows()
    if not rows:
        await callback.answer("No incidents to export yet.", show_alert=True)
        return

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["id", "title", "category", "severity", "status",
                    "reporter", "assignee", "created_at", "updated_at", "description"],
    )
    writer.writeheader()
    writer.writerows(rows)

    filename = f"soc_incidents_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    file = BufferedInputFile(buf.getvalue().encode("utf-8"), filename=filename)
    await callback.message.answer_document(
        file, caption=f"📤 CSV export — {len(rows)} incidents"
    )
    db.log_action(callback.from_user.id, "export_csv", f"count={len(rows)}")
    await callback.answer()


@router.callback_query(F.data == "export:pdf")
@require_role("viewer")
async def export_pdf(callback: CallbackQuery):
    rows = _all_incidents_rows()
    if not rows:
        await callback.answer("No incidents to export yet.", show_alert=True)
        return

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(letter),
        leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("SOC Cyber Defense Commander — Incident Export", styles["Title"]),
        Paragraph(
            f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | {len(rows)} incidents",
            styles["Normal"],
        ),
        Spacer(1, 12),
    ]

    header = ["ID", "Title", "Category", "Severity", "Status", "Reporter", "Assignee", "Opened"]
    table_data = [header]
    for r in rows:
        table_data.append([
            str(r["id"]),
            r["title"][:40],
            r["category"],
            r["severity"].upper(),
            r["status"].upper(),
            r["reporter"] or "-",
            r["assignee"] or "-",
            r["created_at"][:16],
        ])

    severity_colors = {
        "LOW": colors.HexColor("#2ecc71"),
        "MEDIUM": colors.HexColor("#f1c40f"),
        "HIGH": colors.HexColor("#e67e22"),
        "CRITICAL": colors.HexColor("#e74c3c"),
    }

    table = Table(table_data, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    # Color the severity column text based on level
    for i, row in enumerate(table_data[1:], start=1):
        sev = row[3]
        if sev in severity_colors:
            style_commands.append(("TEXTCOLOR", (3, i), (3, i), severity_colors[sev]))
            style_commands.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))

    table.setStyle(TableStyle(style_commands))
    story.append(table)
    doc.build(story)

    filename = f"soc_incidents_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf"
    file = BufferedInputFile(buf.getvalue(), filename=filename)
    await callback.message.answer_document(
        file, caption=f"📤 PDF export — {len(rows)} incidents"
    )
    db.log_action(callback.from_user.id, "export_pdf", f"count={len(rows)}")
    await callback.answer()
