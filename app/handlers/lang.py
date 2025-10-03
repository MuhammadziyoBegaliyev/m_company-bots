# -*- coding: utf-8 -*-
# app/handlers/lang.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from ..locales import L
from ..storage.memory import set_lang, set_profile, is_onboarded
from .onboarding import Onboard                # FSM holati
from .main_menu import show_main_menu          # Asosiy menyuni ko‘rsatish

router = Router()

# Inline tugmalar: lang:uz | lang:ru | lang:en
@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(cb: CallbackQuery, state: FSMContext):
    code = cb.data.split(":", 1)[1]  # "uz", "ru", "en"
    if code not in ("uz", "ru", "en"):
        await cb.answer("Unknown language", show_alert=True)
        return

    # 1) Tilni saqlaymiz (memory + DB)
    set_lang(cb.from_user.id, code)
    set_profile(cb.from_user.id, lang=code)

    t = L.get(code, L["uz"])

    # 2) Tasdiq
    await cb.answer("✅")
    await cb.message.answer(t["chosen"])

    # 3) Onboarding holatiga qarab davom etish
    if not is_onboarded(cb.from_user.id):
        # Ism so‘rash bosqichiga o‘tamiz
        await state.set_state(Onboard.NAME)
        await cb.message.answer(t["ob_ask_name"])
    else:
        # Allaqachon ro‘yxatdan o‘tgan bo‘lsa — asosiy menyu
        await show_main_menu(cb.message, code)
