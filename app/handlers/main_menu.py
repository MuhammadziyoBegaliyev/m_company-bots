

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from ..locales import L
from ..storage.memory import get_lang

router = Router()

def build_main_menu(lang: str) -> ReplyKeyboardMarkup:
    """3-rasmdagi layout: 
       1-qator: [Xizmatlar, Bizning loyihalar]
       2-qator: [Ko'p beriladigan savollar]
       3-qator: [Biz bilan bog'laning, Biz haqimizda]
    """
    t = L.get(lang, L["uz"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["btn_services"]), KeyboardButton(text=t["btn_projects"])],
            [KeyboardButton(text=t["btn_faq"])],
            [KeyboardButton(text=t["btn_contact"]), KeyboardButton(text=t["btn_about"])],
            [KeyboardButton(text=t["btn_audit"])],
        ],
        resize_keyboard=True,
        input_field_placeholder=t.get("main_menu_placeholder") or t.get("menu_title") or "Quyidagi bo'limlardan birini tanlang:"
    )

async def show_main_menu(message: Message, lang: str | None = None) -> None:
    """Asosiy menyuni ko‘rsatish (hint uchun fallback mavjud)."""
    lang = lang or get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    hint = (
        t.get("main_menu_hint")
        or t.get("menu_hint")
        or L["uz"].get("main_menu_hint")
        or "👇 Asosiy menyu:"
    )
    await message.answer(hint, reply_markup=build_main_menu(lang))

# /menu qo‘llab-quvvatlash
@router.message(F.text.in_({"/menu", "menu", "Menu"}))
async def menu_cmd(message: Message):
    await show_main_menu(message)

# “Asosiy menyu”ga qaytish matnlari (welcomeda yoki boshqa joyda text sifatida kelishi mumkin)
_BACK_TEXTS = {
    "uz": {"⬅️ Asosiy menyu"},
    "en": {"⬅️ Main menu"},
    "ru": {"⬅️ Главное меню"},
}
# Uch til matnlarini bitta setga birlashtiramiz
_BACK_SET = set().union(*_BACK_TEXTS.values())

@router.message(F.text.in_(_BACK_SET))
async def back_to_main(message: Message):
    await show_main_menu(message)
