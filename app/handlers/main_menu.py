

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from ..locales import L
from ..storage.memory import get_lang

# Boshqa bo‘limlarga yo‘naltirish uchun importlar
from . import about as about_handlers
from . import projects as projects_handlers
from . import contact as contact_handlers

router = Router()


def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])


# ---------- REPLY (asosiy menyu) ----------
def build_main_kb(lang: str) -> ReplyKeyboardMarkup:
    t = _t(lang)
    rows = [
        [KeyboardButton(text=t["btn_services"]), KeyboardButton(text=t["btn_projects"])],
        [KeyboardButton(text=t["btn_faq"]),      KeyboardButton(text=t["btn_contact"])],
        [KeyboardButton(text=t["btn_about"]),    KeyboardButton(text=t["btn_audit"])],
        [KeyboardButton(text=t["btn_materials"])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ---------- INLINE (welcome ostidagi uchta tugma) ----------
def build_main_inline_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    rows = [
        [InlineKeyboardButton(text=t.get("welcome_btn_about", t["btn_about"]),   callback_data="go:about")],
        [InlineKeyboardButton(text=t.get("welcome_btn_projects", t["btn_projects"]), callback_data="go:projects")],
        [InlineKeyboardButton(text=t.get("welcome_btn_contact", t["btn_contact"]),   callback_data="go:contact")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- start.py uchun soddalashtirilgan interfeys ----------
async def get_main_menu_kb(lang: str, inline: bool = False):
    """inline=True bo‘lsa inline; aks holda reply klaviatura qaytaradi."""
    return build_main_inline_kb(lang) if inline else build_main_kb(lang)


async def show_main_menu(message: Message, lang: str | None = None):
    """Asosiy menyuni reply tugmalar bilan ko‘rsatish."""
    if not lang:
        lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(t.get("menu_hint", "🟡 Asosiy menyu:"), reply_markup=build_main_kb(lang))


# ---------- Inline tugmalardan bo‘limlarga yo‘naltirish ----------
@router.callback_query(F.data == "go:about")
async def go_about(cb: CallbackQuery):
    await cb.answer()
    await about_handlers.about_entry(cb.message)


@router.callback_query(F.data == "go:projects")
async def go_projects(cb: CallbackQuery):
    await cb.answer()
    await projects_handlers.projects_entry(cb.message)


@router.callback_query(F.data == "go:contact")
async def go_contact(cb: CallbackQuery):
    await cb.answer()
    await contact_handlers.contact_entry(cb.message)
