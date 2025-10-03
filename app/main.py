# app/main.py
import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

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
from .handlers import audit as audit_handlers  # ← faqat 1 marta!

def include_once(dp: Dispatcher, router, name: str):
    """Router allaqachon ulangan bo‘lsa xatoga uchramaslik uchun himoya."""
    try:
        dp.include_router(router)
        logger.info(f"✅ Attached router: {name}")
    except RuntimeError as e:
        if "already attached" in str(e):
            logger.warning(f"⚠️ Router already attached, skipping: {name}")
        else:
            raise

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
    include_once(dp, start_handlers.router, "start")
    include_once(dp, lang_handlers.router, "lang")
    include_once(dp, onboarding_handlers.router, "onboarding")
    include_once(dp, main_menu_handlers.router, "main_menu")
    include_once(dp, services_handlers.router, "services")
    include_once(dp, projects_handlers.router, "projects")
    include_once(dp, faq_handlers.router, "faq")
    include_once(dp, contact_handlers.router, "contact")
    include_once(dp, about_handlers.router, "about")
    include_once(dp, audit_handlers.router, "audit")

    logger.info("Bot polling start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[BOT] Stopped")
