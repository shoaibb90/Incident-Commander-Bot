from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import database as db
import keyboards as kb
from states import DetectionScan
from roles import require_role
from detection import analyze_logs
from util import esc
from config import SEVERITY_EMOJI

router = Router()


@router.callback_query(F.data == "menu:scan")
@require_role("analyst")
async def scan_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DetectionScan.waiting_logs)
    await callback.message.edit_text(
        "🔎 <b>Detection Scan</b>\n\n"
        "Paste raw log lines (auth logs, web server logs, firewall logs, etc.) "
        "and I'll run them through the detection rule set — brute force, SQLi, "
        "port scans, download-and-execute, privilege escalation, and more.",
        parse_mode="HTML",
        reply_markup=kb.cancel_kb(),
    )
    await callback.answer()


@router.message(DetectionScan.waiting_logs)
async def scan_run(message: Message, state: FSMContext):
    result = analyze_logs(message.text)
    await state.set_state(None)  # leave the "waiting for logs" state, but keep stored data
    await state.update_data(last_scan=result)

    if not result["findings"]:
        await message.answer(
            f"✅ Scanned {result['total_lines_scanned']} lines — no known attack patterns detected.",
            reply_markup=kb.scan_results_kb(False),
        )
        return

    text = f"⚠️ <b>Scan Results</b> ({result['total_lines_scanned']} lines scanned)\n\n"
    for f in result["findings"]:
        emoji = SEVERITY_EMOJI.get(f["severity"], "")
        text += (
            f"{emoji} <b>{esc(f['name'])}</b> ({f['severity'].upper()})\n"
            f"Category: {esc(f['category'])} | Matches: {f['match_count']}\n"
        )
        for line in f["sample_lines"]:
            text += f"  <code>{esc(line[:80])}</code>\n"
        text += "\n"

    await message.answer(text, parse_mode="HTML", reply_markup=kb.scan_results_kb(True))


@router.callback_query(F.data == "scan:create_incident")
@require_role("analyst")
async def create_incident_from_scan(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    result = data.get("last_scan")
    if not result or not result["findings"]:
        await callback.answer("No recent scan results found.", show_alert=True)
        return

    top = max(result["findings"], key=lambda f: {"low": 0, "medium": 1, "high": 2, "critical": 3}[f["severity"]])
    reporter = db.get_user(callback.from_user.id)
    description = "Auto-generated from detection scan:\n\n"
    for f in result["findings"]:
        description += f"- {f['name']} ({f['severity']}, {f['match_count']} matches)\n"

    incident_id = db.create_incident(
        title=f"Detection scan: {top['name']}",
        description=description,
        category=top["category"],
        severity=top["severity"],
        reporter_id=reporter["id"],
    )
    db.log_action(callback.from_user.id, "incident_created_from_scan", f"id={incident_id}")
    await callback.message.edit_text(
        f"✅ Incident <b>#{incident_id}</b> created from scan findings.",
        parse_mode="HTML",
        reply_markup=kb.incident_detail_kb(incident_id, is_admin=(reporter["role"] == "admin"), is_analyst=True),
    )
    await callback.answer()
