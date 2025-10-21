import os
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from loguru import logger

from ..locales import L
from ..config import settings
from ..storage.db import db
from ..storage.memory import get_lang
from .main_menu import get_main_menu_kb, show_main_menu
from .onboarding import start_onboarding

router = Router()
logger.info("🏁 Start router initialized")

WELCOME_PHOTO = "app/assets/welcome.jpg"

# >>> bu bayroq orqali xulq-atvorni boshqarasiz
ALWAYS_ASK_LANG_ON_START = True


def _lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ]])


async def _show_welcome(message: Message, lang: str):
    t = L.get(lang, L["uz"])
    caption = t.get("welcome_caption", "M company'ga xush kelibsiz!")
    
    inline_kb = await get_main_menu_kb(lang, inline=True)
    
    if os.path.isfile(WELCOME_PHOTO):
        try:
            await message.answer_photo(
                photo=FSInputFile(WELCOME_PHOTO),
                caption=caption,
                reply_markup=inline_kb,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Welcome photo send failed: {e}")
            await message.answer(caption, reply_markup=inline_kb, parse_mode="HTML")
    else:
        await message.answer(caption, reply_markup=inline_kb, parse_mode="HTML")
    
    # Reply asosiy menyu
    await show_main_menu(message, lang)


# ===== ASOSIY START HANDLER =====
@router.message(CommandStart())
async def start(message: Message, command: CommandObject):
    """
    /start handler - har qanday /start ni ushlaydi
    (deep_link=True ni o'chirish orqali)
    """
    user = message.from_user
    
    logger.info(f"🏁 /start from user {user.id} (@{user.username or 'none'})")
    
    if user is None:
        await message.answer("User information not found. Please try again.")
        return
    
    # Deep link payload (agar mavjud bo'lsa)
    payload = (command.args or "").strip().lower()
    if payload:
        logger.info(f"   Deep link payload: {payload}")
    
    # DB'da foydalanuvchini yaratib qo'yamiz (agar bo'lmasa)
    try:
        db.upsert_user(
            user_id=user.id,
            username=user.username or None,
            name=(user.full_name or "").strip() or None,
        )
        logger.debug(f"   User {user.id} upserted to DB")
    except Exception as e:
        logger.error(f"DB upsert_user failed: {e}")
    
    # DB'dagi holat
    u = db.get_user(user.id) or {}
    saved_lang = (u.get("lang") or "").strip().lower()
    onboarded = bool(u.get("onboarded", 0))
    
    logger.info(f"   Saved lang: {saved_lang or 'none'}, Onboarded: {onboarded}")
    
    # 1) Til oynasini ko'rsatish shartlari
    need_lang = (
        ALWAYS_ASK_LANG_ON_START
        or not saved_lang
        or payload in {"lang", "language", "setup"}
    )
    
    if need_lang:
        # Hozircha faqat til oynasini ko'rsatamiz — user tilni bosgandan so'ng
        # lang.py onboardingni chaqiradi (agar onboarded=0 bo'lsa)
        t0 = L.get(saved_lang or get_lang(user.id, settings.DEFAULT_LANG), L["uz"])
        logger.info(f"   Showing language selection")
        await message.answer(
            t0.get("choose_lang", "Tilni tanlang:"), 
            reply_markup=_lang_kb()
        )
        return
    
    # 2) Til bor, onboarding tugallanmagan — welcome + onboarding
    if not onboarded:
        logger.info(f"   Showing welcome + starting onboarding")
        await _show_welcome(message, saved_lang or "uz")
        await start_onboarding(message, saved_lang or "uz")
        return
    
    # 3) Hammasi bor — welcome + menyu
    logger.info(f"   Showing welcome + main menu")
    await _show_welcome(message, saved_lang or "uz")