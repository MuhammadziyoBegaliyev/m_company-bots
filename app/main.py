import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .handlers import start as start_handlers
from .handlers import lang as lang_handlers
from .handlers import services as services_handlers
from .handlers import projects as projects_handlers
from .handlers import faq as faq_handlers
from .handlers import contact as contact_handlers
from .handlers import about as about_handlers


async def main():
    logger.add("bot.log", rotation="1 week", level="INFO")


    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())


    # Routerlarni tartib bilan ulaymiz
    dp.include_router(start_handlers.router)
    dp.include_router(lang_handlers.router)
    dp.include_router(services_handlers.router)
    dp.include_router(projects_handlers.router)
    dp.include_router(faq_handlers.router)
    dp.include_router(contact_handlers.router)
    dp.include_router(about_handlers.router)


    logger.info("Bot polling start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[BOT] Stopped")  