import io
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
import database as db
import keyboards as kb
from config import SEVERITY_EMOJI, STATUS_EMOJI

router = Router()


@router.callback_query(F.data == "menu:reports")
async def reports_menu(callback: CallbackQuery):
    stats = db.get_stats()
    text = "📊 <b>SOC Dashboard</b>\n\n"
    text += f"Total incidents: <b>{stats['total']}</b>\n\n"
    text += "<b>By status:</b>\n"
    for status, emoji in STATUS_EMOJI.items():
        n = stats["by_status"].get(status, 0)
        text += f"{emoji} {status.capitalize()}: {n}\n"
    text += "\n<b>By severity:</b>\n"
    for sev, emoji in SEVERITY_EMOJI.items():
        n = stats["by_severity"].get(sev, 0)
        text += f"{emoji} {sev.capitalize()}: {n}\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.reports_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("incident:report:"))
async def generate_report(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    inc = db.get_incident(incident_id)
    if not inc:
        await callback.answer("Incident not found.", show_alert=True)
        return
    notes = db.get_notes(incident_id)
    reporter = db.get_user_by_id(inc["reporter_id"])
    assignee = db.get_user_by_id(inc["assigned_to"]) if inc["assigned_to"] else None

    lines = [
        "SOC INCIDENT REPORT",
        "=" * 40,
        f"Incident ID: #{inc['id']}",
        f"Title: {inc['title']}",
        f"Category: {inc['category']}",
        f"Severity: {inc['severity'].upper()}",
        f"Status: {inc['status'].upper()}",
        f"Reported by: {reporter['username'] if reporter else 'unknown'}",
        f"Assigned to: {assignee['username'] if assignee else 'unassigned'}",
        f"Opened: {inc['created_at']}",
        f"Last updated: {inc['updated_at']}",
        "",
        "DESCRIPTION",
        "-" * 40,
        inc["description"],
        "",
        "INVESTIGATION TIMELINE",
        "-" * 40,
    ]
    if notes:
        for n in notes:
            author = db.get_user_by_id(n["author_id"])
            aname = author["username"] if author else "unknown"
            lines.append(f"[{n['created_at']}] {aname}: {n['note']}")
    else:
        lines.append("No investigation notes recorded.")

    report_text = "\n".join(lines)
    file = BufferedInputFile(report_text.encode("utf-8"), filename=f"incident_{incident_id}_report.txt")
    await callback.message.answer_document(file, caption=f"📄 Report for incident #{incident_id}")
    db.log_action(callback.from_user.id, "report_generated", f"id={incident_id}")
    await callback.answer()
