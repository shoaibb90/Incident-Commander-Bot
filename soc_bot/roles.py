from functools import wraps
from aiogram.types import Message, CallbackQuery
import database as db
from config import ROLE_LEVELS


def user_level(telegram_id):
    user = db.get_user(telegram_id)
    if not user:
        return 0
    return ROLE_LEVELS.get(user["role"], 0)


def require_role(min_role):
    """Decorator for message/callback handlers. Blocks users below min_role."""
    min_level = ROLE_LEVELS[min_role]

    def decorator(handler):
        @wraps(handler)
        async def wrapper(event, *args, **kwargs):
            telegram_id = event.from_user.id
            level = user_level(telegram_id)
            if level < min_level:
                text = (
                    "🚫 You don't have permission for this action.\n"
                    f"Required role: <b>{min_role}</b> or higher."
                )
                if isinstance(event, CallbackQuery):
                    await event.answer("Access denied", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(text, parse_mode="HTML")
                return
            return await handler(event, *args, **kwargs)
        return wrapper
    return decorator
