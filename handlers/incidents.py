from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import database as db
import keyboards as kb
from states import NewIncident, AddNote
from roles import require_role, user_level
from util import esc
from config import ROLE_LEVELS, SEVERITY_EMOJI, STATUS_EMOJI

router = Router()


def role_of(telegram_id):
    u = db.get_user(telegram_id)
    return u["role"] if u else "pending"


# ---------- Menu & listing ----------

@router.callback_query(F.data == "menu:incidents")
async def incidents_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 <b>Incident Management</b>", parse_mode="HTML", reply_markup=kb.incidents_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("incident:list:"))
async def list_incidents(callback: CallbackQuery):
    filt = callback.data.split(":")[2]
    status = None if filt == "all" else filt
    incidents = db.list_incidents(status=status)
    if not incidents:
        await callback.message.edit_text(
            "No incidents found in this category.", reply_markup=kb.incidents_menu()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        f"📂 <b>Incidents</b> ({len(incidents)} found)\nTap one to view details.",
        parse_mode="HTML",
        reply_markup=kb.incident_list_kb(incidents),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("incident:view:"))
async def view_incident(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    inc = db.get_incident(incident_id)
    if not inc:
        await callback.answer("Incident not found.", show_alert=True)
        return
    notes = db.get_notes(incident_id)
    reporter = db.get_user_by_id(inc["reporter_id"])
    assignee = db.get_user_by_id(inc["assigned_to"]) if inc["assigned_to"] else None

    text = (
        f"{STATUS_EMOJI.get(inc['status'],'')} <b>Incident #{inc['id']}: {esc(inc['title'])}</b>\n\n"
        f"Severity: {SEVERITY_EMOJI.get(inc['severity'],'')} {esc(inc['severity'].capitalize())}\n"
        f"Category: {esc(inc['category'])}\n"
        f"Status: {esc(inc['status'].capitalize())}\n"
        f"Reported by: @{esc(reporter['username']) if reporter else 'unknown'}\n"
        f"Assigned to: {'@' + esc(assignee['username']) if assignee else '—'}\n"
        f"Opened: {esc(inc['created_at'][:16])}\n"
        f"Last updated: {esc(inc['updated_at'][:16])}\n\n"
        f"📝 <b>Description:</b>\n{esc(inc['description'])}\n\n"
        f"🗒 <b>Notes ({len(notes)}):</b>\n"
    )
    if notes:
        for n in notes[-5:]:
            author = db.get_user_by_id(n["author_id"])
            aname = author["username"] if author else "?"
            text += f"• [{esc(n['created_at'][:16])}] @{esc(aname)}: {esc(n['note'])}\n"
    else:
        text += "No notes yet.\n"

    role = role_of(callback.from_user.id)
    level = ROLE_LEVELS[role]
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.incident_detail_kb(
            incident_id,
            is_admin=(role == "admin"),
            is_analyst=(level >= ROLE_LEVELS["analyst"]),
        ),
    )
    await callback.answer()


# ---------- Create incident (FSM wizard) ----------

@router.callback_query(F.data == "incident:new")
@require_role("analyst")
async def new_incident_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewIncident.title)
    await callback.message.edit_text(
        "➕ <b>New Incident</b>\n\nSend me a short <b>title</b> for this incident.",
        parse_mode="HTML",
        reply_markup=kb.cancel_kb(),
    )
    await callback.answer()


@router.message(NewIncident.title)
async def new_incident_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewIncident.description)
    await message.answer("Now send a <b>description</b> of what happened.", parse_mode="HTML")


@router.message(NewIncident.description)
async def new_incident_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(NewIncident.category)
    await message.answer("Pick a <b>category</b>:", parse_mode="HTML", reply_markup=kb.category_picker())


@router.callback_query(NewIncident.category, F.data.startswith("newinc:cat:"))
async def new_incident_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[2]
    await state.update_data(category=category)
    await state.set_state(NewIncident.severity)
    await callback.message.edit_text(
        "Pick a <b>severity</b>:", parse_mode="HTML", reply_markup=kb.severity_picker()
    )
    await callback.answer()


@router.callback_query(NewIncident.severity, F.data.startswith("newinc:sev:"))
async def new_incident_severity(callback: CallbackQuery, state: FSMContext):
    severity = callback.data.split(":")[2]
    data = await state.get_data()
    reporter = db.get_user(callback.from_user.id)
    incident_id = db.create_incident(
        title=data["title"],
        description=data["description"],
        category=data["category"],
        severity=severity,
        reporter_id=reporter["id"],
    )
    db.log_action(callback.from_user.id, "incident_created", f"id={incident_id}")
    await state.clear()
    await callback.message.edit_text(
        f"✅ Incident <b>#{incident_id}</b> created and logged.",
        parse_mode="HTML",
        reply_markup=kb.incident_detail_kb(incident_id, is_admin=(reporter["role"] == "admin"), is_analyst=True),
    )
    await callback.answer()


# ---------- Actions on an existing incident ----------

@router.callback_query(F.data.startswith("incident:investigate:"))
@require_role("analyst")
async def investigate(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    db.update_incident_status(incident_id, "investigating")
    db.log_action(callback.from_user.id, "incident_investigating", f"id={incident_id}")
    await callback.answer("Status set to Investigating")
    await view_incident(callback)


@router.callback_query(F.data.startswith("incident:resolve:"))
@require_role("analyst")
async def resolve(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    db.update_incident_status(incident_id, "resolved")
    db.log_action(callback.from_user.id, "incident_resolved", f"id={incident_id}")
    await callback.answer("Marked resolved ✅")
    await view_incident(callback)


@router.callback_query(F.data.startswith("incident:assign_me:"))
@require_role("analyst")
async def assign_me(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    user = db.get_user(callback.from_user.id)
    db.assign_incident(incident_id, user["id"])
    db.log_action(callback.from_user.id, "incident_assigned_self", f"id={incident_id}")
    await callback.answer("Assigned to you")
    await view_incident(callback)


@router.callback_query(F.data.startswith("incident:note:"))
@require_role("analyst")
async def note_start(callback: CallbackQuery, state: FSMContext):
    incident_id = int(callback.data.split(":")[2])
    await state.update_data(incident_id=incident_id)
    await state.set_state(AddNote.waiting_note)
    await callback.message.edit_text(
        "📝 Send the note text to add to this incident.", reply_markup=kb.cancel_kb()
    )
    await callback.answer()


@router.message(AddNote.waiting_note)
async def note_save(message: Message, state: FSMContext):
    data = await state.get_data()
    user = db.get_user(message.from_user.id)
    db.add_note(data["incident_id"], user["id"], message.text)
    db.log_action(message.from_user.id, "note_added", f"id={data['incident_id']}")
    await state.clear()
    await message.answer(
        "✅ Note added.",
        reply_markup=kb.incident_detail_kb(data["incident_id"], is_admin=(user["role"] == "admin"), is_analyst=True),
    )


@router.callback_query(F.data.startswith("incident:delete:"))
@require_role("admin")
async def delete_confirm_prompt(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        f"⚠️ Delete incident #{incident_id}? This cannot be undone.",
        reply_markup=kb.confirm_delete_kb(incident_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("incident:delete_confirm:"))
@require_role("admin")
async def delete_incident(callback: CallbackQuery):
    incident_id = int(callback.data.split(":")[2])
    db.delete_incident(incident_id)
    db.log_action(callback.from_user.id, "incident_deleted", f"id={incident_id}")
    await callback.answer("Deleted")
    await callback.message.edit_text("🗑 Incident deleted.", reply_markup=kb.incidents_menu())
