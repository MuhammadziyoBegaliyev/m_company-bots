# app/main.py
import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from .storage.db import db
from .config import settings

# HANDLERLAR — faqat bitta marta import qiling!
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
from .handlers import admin as admin_handlers  # admin panel
from .handlers import materials as materials_handlers

def include_once(dp: Dispatcher, router, name: str) -> None:
    """Router allaqachon ulangan bo‘lsa xatoga uchramaslik uchun himoya."""
    try:
        dp.include_router(router)
        logger.info(f"✅ Attached router: {name}")
    except RuntimeError as e:
        msg = str(e).lower()
        if "already attached" in msg:
            logger.warning(f"⚠️ Router already attached, skipping: {name}")
        else:
            raise

async def main():
    logger.add("bot.log", rotation="1 week", level=settings.LOG_LEVEL)
    try:  # ->DB
        db.init()
        logger.info("DB initialized")
    except Exception as e:
        logger.warning(f"DB init skipped: {e}")
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlar tartibi:
    include_once(dp, start_handlers.router, "start")          # /start + tilni tanlash ko‘rsatish
    include_once(dp, lang_handlers.router, "lang")            # lang:xx callback
    include_once(dp, onboarding_handlers.router, "onboarding")# ism/telefon FSM
    include_once(dp, main_menu_handlers.router, "main_menu")  # asosiy menyu
    include_once(dp, services_handlers.router, "services")
    include_once(dp, projects_handlers.router, "projects")
    include_once(dp, faq_handlers.router, "faq")
    include_once(dp, contact_handlers.router, "contact")
    include_once(dp, about_handlers.router, "about")
    include_once(dp, audit_handlers.router, "audit")
    include_once(dp, materials_handlers.router, "materials")
    include_once(dp, admin_handlers.router, "admin")          # ✅ shu yerda ham include_once

    logger.info("Bot polling start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[BOT] Stopped")
