import os
from pathlib import Path
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

# Nisbiy yo'l - loyiha strukturasiga bog'liq
BASE_DIR = Path(__file__).resolve().parent.parent
WELCOME_PHOTO = BASE_DIR / "assets" / "welcome.png"

# >>> bu bayroq orqali xulq-atvorni boshqarasiz
# False qilsangiz - faqat yangi userlar uchun til so'raladi
ALWAYS_ASK_LANG_ON_START = False


def _lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 Oʻz", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Ру", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 Eng", callback_data="lang:en"),
    ]])


async def _show_welcome(message: Message, lang: str):
    t = L.get(lang, L["uz"])
    caption = t.get("welcome_caption", "M company'ga xush kelibsiz!")
    
    inline_kb = await get_main_menu_kb(lang, inline=True)
    
    # DEBUG: Faylni tekshirish
    photo_path = str(WELCOME_PHOTO)
    logger.info(f"📸 Checking welcome photo: {photo_path}")
    logger.info(f"📸 File exists: {WELCOME_PHOTO.exists()}")
    logger.info(f"📸 File is file: {WELCOME_PHOTO.is_file()}")
    logger.info(f"📸 Current working dir: {os.getcwd()}")
    logger.info(f"📸 BASE_DIR: {BASE_DIR}")
    
    # Rasmni yuborish
    photo_sent = False
    if WELCOME_PHOTO.exists() and WELCOME_PHOTO.is_file():
        try:
            # Fayl o'lchamini tekshirish
            file_size = WELCOME_PHOTO.stat().st_size
            logger.info(f"📸 File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
            
            # Telegram 10MB dan kichik bo'lishi kerak
            if file_size > 10 * 1024 * 1024:
                logger.error(f"❌ Photo too large: {file_size / (1024*1024):.2f} MB")
                raise ValueError("Photo file too large")
            
            photo = FSInputFile(str(WELCOME_PHOTO))
            
            # Avval faqat rasm yuboramiz
            msg = await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode="HTML",
            )
            logger.info(f"📸 Welcome photo sent successfully! msg_id={msg.message_id}")
            photo_sent = True
            
            # Keyin inline keyboard alohida yuboramiz
            await message.answer(
                "Quyidagilardan birini tanlang:",
                reply_markup=inline_kb
            )
            
        except Exception as e:
            logger.error(f"❌ Welcome photo send failed: {e}", exc_info=True)
    else:
        logger.warning(f"⚠️ Welcome photo not found at: {WELCOME_PHOTO}")
    
    # Agar rasm yuborilmagan bo'lsa, faqat matn yuboramiz
    if not photo_sent:
        await message.answer(caption, reply_markup=inline_kb, parse_mode="HTML")
    
    # Reply asosiy menyu
    await show_main_menu(message, lang)


# ===== ASOSIY START HANDLER =====
@router.message(CommandStart())
async def start(message: Message, command: CommandObject):
    """
    /start handler - har qanay /start ni ushlaydi
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