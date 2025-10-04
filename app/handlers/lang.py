# app/handlers/lang.py
from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..locales import L
from ..handlers.main_menu import build_main_menu
from ..keyboards.inline import WELCOME_KB
from ..storage.memory import get_lang as mem_get_lang

try:
    from ..storage.memory import set_lang as mem_set_lang
except Exception:
    def mem_set_lang(uid: int, lang: str): pass

try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

@router.callback_query(F.data.startswith("lang:"))
async def choose_lang(cb: CallbackQuery):
    lang = cb.data.split(":")[-1]
    if lang not in ("uz", "en", "ru"):
        lang = "uz"

    mem_set_lang(cb.from_user.id, lang)
    if db:
        db.init()
        db.upsert_user(
            user_id=cb.from_user.id,
            username=cb.from_user.username or None,
            name=cb.from_user.full_name or None,
            lang=lang,
        )

    t = _t(lang)
    await cb.answer(t.get("lang_ok", "✅ Saved"))

    # 1) Welcome kartasi: rasm + caption + 3ta inline tugma
    caption = t.get("welcome_caption") or ""
    photo_paths = ["app/assets/welcome.png", "app/assets/about.png"]
    sent = False
    for p in photo_paths:
        try:
            await cb.message.answer_photo(photo=p, caption=caption, parse_mode="HTML",
                                          reply_markup=WELCOME_KB(lang))
            sent = True
            break
        except Exception:
            continue
    if not sent:
        await cb.message.answer(caption, parse_mode="HTML", reply_markup=WELCOME_KB(lang))

    # 2) Keyin — Asosiy menyu
    await cb.message.answer(t.get("menu_hint", "🟡 Asosiy menyu:"),
                            reply_markup=build_main_menu(lang))


# Welcome tugmalari (soddalashtirilgan ko‘rinish)
@router.callback_query(F.data == "welcome:about")
async def welcome_about(cb: CallbackQuery):
    lang = mem_get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await cb.answer()
    await cb.message.answer(t.get("stub", "Bu bo'lim tez orada to'ldiriladi. 🙌"))

@router.callback_query(F.data == "welcome:projects")
async def welcome_projects(cb: CallbackQuery):
    lang = mem_get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await cb.answer()
    await cb.message.answer(t.get("projects_title", "Bizning loyihalar"))

@router.callback_query(F.data == "welcome:contact")
async def welcome_contact(cb: CallbackQuery):
    lang = mem_get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await cb.answer()
    await cb.message.answer(t.get("contact_title", "Biz bilan bog‘laning"))
