import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import main_router

logging.basicConfig(level=logging.INFO)


async def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        raise SystemExit(
            "No bot token set. Create a .env file with BOT_TOKEN=your_token_here "
            "(get one from @BotFather on Telegram)."
        )

    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)

    logging.info("SOC Cyber Defense Commander bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if name == "main":
    asyncio.run(main())
