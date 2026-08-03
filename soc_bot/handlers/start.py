from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
import database as db
import keyboards as kb
from util import esc

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        role = db.create_user(
            message.from_user.id, message.from_user.username, message.from_user.full_name
        )
        db.log_action(message.from_user.id, "user_registered", f"role={role}")
        if role == "admin":
            await message.answer(
                "🛡️ <b>SOC Cyber Defense Commander</b>\n\n"
                "You're the first user — you've been made <b>Admin</b> automatically.\n"
                "Use the Admin Panel to approve new analysts as they join.",
                parse_mode="HTML",
                reply_markup=kb.main_menu(is_admin=True),
            )
            return
        else:
            await message.answer(
                "🛡️ <b>SOC Cyber Defense Commander</b>\n\n"
                "Your account has been created but is <b>pending approval</b>.\n"
                "An admin needs to approve you before you can use the system.",
                parse_mode="HTML",
            )
            return

    if user["role"] == "pending":
        await message.answer(
            "⏳ Your account is still pending admin approval. Please wait."
        )
        return

    await message.answer(
        f"🛡️ Welcome back, <b>{esc(message.from_user.full_name)}</b>.\n"
        f"Role: <b>{esc(user['role'].capitalize())}</b>",
        parse_mode="HTML",
        reply_markup=kb.main_menu(is_admin=(user["role"] == "admin")),
    )


@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    is_admin = user and user["role"] == "admin"
    await callback.message.edit_text(
        "🛡️ <b>SOC Cyber Defense Commander — Main Menu</b>",
        parse_mode="HTML",
        reply_markup=kb.main_menu(is_admin=is_admin),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def profile(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    stats = db.get_stats()
    text = (
        f"👤 <b>Profile</b>\n\n"
        f"Name: {esc(user['full_name'])}\n"
        f"Username: @{esc(user['username'])}\n"
        f"Role: <b>{esc(user['role'].capitalize())}</b>\n"
        f"Member since: {esc(user['created_at'][:10])}\n\n"
        f"📊 System-wide: {stats['total']} total incidents logged"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_button())
    await callback.answer()
