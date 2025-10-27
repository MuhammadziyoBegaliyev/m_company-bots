# -*- coding: utf-8 -*-
# app/main.py

import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .storage.db import db

# --- Handlers (har biri faqat bir marta import qilinadi) ---
from .handlers import start as start_handlers
from .handlers import lang as lang_handlers
from .handlers import onboarding as onboarding_handlers
from .handlers import main_menu as main_menu_handlers
from .handlers import services as services_handlers
from .handlers import projects as projects_handlers
from .handlers import faq as faq_handlers
from .handlers import contact as contact_handlers
from .handlers import about as about_handlers
from .handlers import materials as materials_handlers
from .handlers import audit as audit_handlers
from .handlers import admin as admin_handlers  # umumiy admin panel

# ixtiyoriy modullar — mavjud bo‘lsa ulanadi
try:
    from .handlers import admin_materials as admin_materials_handlers
except Exception:
    admin_materials_handlers = None  # type: ignore

try:
    from .handlers import debug_handler
except Exception:
    debug_handler = None  # type: ignore


def include_once(dp: Dispatcher, router, name: str) -> None:
    """Router allaqachon ulangan bo‘lsa xato bermaslik uchun himoya."""
    if router is None:
        logger.warning(f"⚠️ Router is None, skipping: {name}")
        return
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
    # ---------- Logging ----------
    logger.remove()
    logger.add("bot.log", rotation="1 week", level=settings.LOG_LEVEL)
    logger.add(lambda m: print(m, end=""))  # konsolga ham chiqaramiz

    # ---------- Config snapshot ----------
    logger.info("=" * 64)
    logger.info("⚙️  BOT CONFIG")
    safe_token = (settings.BOT_TOKEN[:8] + "…") if settings.BOT_TOKEN else "❌ MISSING"
    logger.info(f"🤖 Token: {safe_token}")
    logger.info(f"👥 Admin IDs: {settings.admin_ids} (count={len(settings.admin_ids)})")
    logger.info(f"💾 DB URL: {settings.DATABASE_URL}")
    logger.info(f"🔊 Log level: {settings.LOG_LEVEL}")
    logger.info("=" * 64)

    if not settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env ni tekshiring.")

    # ---------- DB init ----------
    try:
        db.init()
        logger.info("✅ DB initialized")
    except Exception as e:
        logger.warning(f"⚠️ DB init skipped: {e}")

    # ---------- Bot & Dispatcher ----------
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # ---------- Routers order (MUHIM!) ----------
    # Eslatma:
    # 1) admin_materials -> debug_handler dan oldin bo‘lishi shart,
    #    aks holda 'adm:mats' va 'madmin:*' callbacklari debugga tushib ketadi.
    # 2) admin panel (admin_handlers) menyudagi tugmalarni beradi,
    #    admin_materials esa 'adm:mats' callbackini qabul qiladi – tartib mos.

    # Kontent va foydalanuvchi oqimi
    include_once(dp, start_handlers.router, "start")
    include_once(dp, lang_handlers.router, "lang")
    include_once(dp, onboarding_handlers.router, "onboarding")
    include_once(dp, main_menu_handlers.router, "main_menu")
    include_once(dp, services_handlers.router, "services")
    include_once(dp, projects_handlers.router, "projects")
    include_once(dp, faq_handlers.router, "faq")
    include_once(dp, contact_handlers.router, "contact")
    include_once(dp, about_handlers.router, "about")
    include_once(dp, materials_handlers.router, "materials")
    include_once(dp, audit_handlers.router, "audit")

    # Adminlar: avval materiallar modulini, keyin umumiy admin panelni ulaymiz
    if admin_materials_handlers is not None:
        include_once(dp, admin_materials_handlers.router, "admin_materials")
    include_once(dp, admin_handlers.router, "admin")

    # Catch-all / diagnostika — ENG OXIRIDA!
    if debug_handler is not None:
        include_once(dp, debug_handler.router, "debug_catchall")
        logger.warning("⚠️ DEBUG CATCH-ALL ENABLED")

    # ---------- Start polling ----------
    logger.info("=" * 64)
    logger.info("🚀 Bot polling starting…")
    allowed_updates = dp.resolve_used_update_types()
    logger.info(f"📡 Allowed updates: {allowed_updates}")
    await dp.start_polling(bot, allowed_updates=allowed_updates)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("[BOT] Stopped")
