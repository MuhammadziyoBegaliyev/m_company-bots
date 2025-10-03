# app/main.py
import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings

# HANDLERLAR — faqat bitta marta import va include!
from .handlers import start as start_handlers
from .handlers import lang as lang_handlers
from .handlers import onboarding as onboarding_handlers
from .handlers import main_menu as main_menu_handlers
from .handlers import services as services_handlers
from .handlers import projects as projects_handlers
from .handlers import faq as faq_handlers
from .handlers import contact as contact_handlers
from .handlers import about as about_handlers
from .handlers import audit as audit_handlers
from .handlers import audit as audit_handlers

async def main():
    logger.add("bot.log", rotation="1 week", level="INFO")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlar tartibi:
    # 1) /start — salom + til tanlash tugmalari
    # 2) lang:xx — til callback’i
    # 3) onboarding (ism/telefon)
    # 4) qolgan bo‘limlar
    dp.include_router(start_handlers.router)
    dp.include_router(lang_handlers.router)
    dp.include_router(onboarding_handlers.router)
    dp.include_router(main_menu_handlers.router)
    dp.include_router(services_handlers.router)
    dp.include_router(projects_handlers.router)
    dp.include_router(faq_handlers.router)
    dp.include_router(contact_handlers.router)
    dp.include_router(about_handlers.router)
    dp.include_router(audit_handlers.router)
    dp.include_router(audit_handlers.router)

    logger.info("Bot polling start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[BOT] Stopped")
