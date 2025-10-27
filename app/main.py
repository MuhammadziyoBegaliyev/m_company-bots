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

# --- Handlers (bir martalik import) ---
from .handlers import admin as admin_handlers                  # /admin — BIRINCHI
from .handlers import materials as materials_handlers
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

# Ixtiyoriy modullar
try:
    from .handlers import admin_materials as admin_materials_handlers  # adm:mats / madmin:*
except Exception:
    admin_materials_handlers = None  # type: ignore

try:
    from .handlers import debug_handler  # catch-all logger
except Exception:
    debug_handler = None  # type: ignore


# ---------- Routerni faqat bir marta ulash helperi ----------
_INCLUDED: set[int] = set()

def include_once(dp: Dispatcher, router, name: str) -> None:
    """Router allaqachon ulangan bo‘lsa, takror ulashga yo‘l qo‘ymaydi."""
    if router is None:
        return
    r_id = id(router)
    if r_id in _INCLUDED:
        logger.warning(f"⚠️ Router already attached, skipping: {name}")
        return
    dp.include_router(router)
    _INCLUDED.add(r_id)
    logger.info(f"✅ Attached router: {name}")


async def main():
    # ---------- Logging ----------
    logger.remove()
    logger.add("bot.log", rotation="1 week", level=settings.LOG_LEVEL)
    logger.add(lambda m: print(m, end=""))  # konsolga ham yozamiz

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

    # ---------- MUHIM: Routerlar tartibi ----------
    # 1) Admin panel — har doim birinchi
    include_once(dp, admin_handlers.router, "admin")

    # 2) Admin materiallar — admindan keyin, debugdan oldin
    if admin_materials_handlers is not None:
        include_once(dp, admin_materials_handlers.router, "admin_materials")

    # 3) Foydalanuvchi oqimi routerlari
    include_once(dp, materials_handlers.router, "materials")
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

    # 4) Catch-all/diagnostika — ENG OXIRIDA!
    if debug_handler is not None:
        include_once(dp, debug_handler.router, "debug_catchall")
        logger.warning("⚠️ DEBUG CATCH-ALL ENABLED")

    # ---------- Polling ----------
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
