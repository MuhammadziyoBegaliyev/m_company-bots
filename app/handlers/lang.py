# app/handlers/lang.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from ..locales import L
from ..storage.memory import get_lang
from ..handlers.main_menu import build_main_kb, show_main_menu

# agar DB bilan ham tilni saqlamoqchi bo'lsangiz:
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

@router.callback_query(F.data.startswith("lang:"))
async def set_lang_handler(cb: CallbackQuery):
    code = cb.data.split(":", 1)[1]  # uz | en | ru
    if code not in ("uz", "en", "ru"):
        code = "uz"

    # memory va DB da saqlash (agar bor bo'lsa)
    try:
        from ..storage.memory import set_lang as mem_set_lang
        mem_set_lang(cb.from_user.id, code)
    except Exception:
        pass
    if db:
        try:
            db.set_lang(cb.from_user.id, code)
        except Exception:
            pass

    t = L.get(code, L["uz"])
    # “til tanlandi” xabari + reply klaviatura
    await cb.message.answer(t.get("chosen", "✅ Tanlandi"), reply_markup=build_main_kb(code))
    await cb.answer()

    # xohlasangiz, darhol asosiy menyuni ham ko'rsatasiz:
    await show_main_menu(cb.message, code)
