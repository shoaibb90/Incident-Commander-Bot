from aiogram import Router, F
from aiogram.types import CallbackQuery
import database as db
import keyboards as kb
from roles import require_role
from util import esc

router = Router()


@router.callback_query(F.data == "menu:admin")
@require_role("admin")
async def admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Admin Panel</b>", parse_mode="HTML", reply_markup=kb.admin_panel_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:pending")
@require_role("admin")
async def pending_users(callback: CallbackQuery):
    users = db.list_users(role_filter="pending")
    if not users:
        await callback.message.edit_text(
            "No pending approvals. ✅", reply_markup=kb.admin_panel_kb()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        f"👥 <b>Pending Approvals</b> ({len(users)})",
        parse_mode="HTML",
        reply_markup=kb.pending_users_kb(users),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:approve:"))
@require_role("admin")
async def approve_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[2])
    user = db.get_user_by_id(user_id)
    db.set_role(user["telegram_id"], "viewer")
    db.log_action(callback.from_user.id, "user_approved", f"user_id={user_id}")
    await callback.answer("Approved as Viewer")
    await pending_users(callback)


@router.callback_query(F.data == "admin:roles")
@require_role("admin")
async def manage_roles(callback: CallbackQuery):
    users = [u for u in db.list_users() if u["role"] != "pending"]
    await callback.message.edit_text(
        "🎭 <b>Manage Roles</b>\nTap a user to change their role.",
        parse_mode="HTML",
        reply_markup=kb.users_list_kb(users, action="setrole_pick"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:setrole_pick:"))
@require_role("admin")
async def pick_new_role(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "Choose new role:", reply_markup=kb.role_picker(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:setrole:"))
@require_role("admin")
async def set_role(callback: CallbackQuery):
    _, _, user_id, role = callback.data.split(":")
    user = db.get_user_by_id(int(user_id))
    db.set_role(user["telegram_id"], role)
    db.log_action(callback.from_user.id, "role_changed", f"user_id={user_id} new_role={role}")
    await callback.answer(f"Role updated to {role}")
    await manage_roles(callback)


@router.callback_query(F.data == "admin:audit")
@require_role("admin")
async def audit_log(callback: CallbackQuery):
    entries = db.get_audit_log(limit=15)
    if not entries:
        text = "📜 <b>Audit Log</b>\n\nNo actions recorded yet."
    else:
        text = "📜 <b>Audit Log</b> (last 15 actions)\n\n"
        for e in entries:
            actor = db.get_user(e["actor_id"])
            aname = actor["username"] if actor else str(e["actor_id"])
            text += f"• [{esc(e['created_at'][:16])}] @{esc(aname)}: {esc(e['action'])} {esc(e['details'])}\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.admin_panel_kb())
    await callback.answer()
