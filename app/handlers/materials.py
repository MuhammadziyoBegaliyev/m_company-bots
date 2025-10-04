# app/handlers/materials.py
from aiogram import Router, F
from aiogram.types import Message
from ..locales import L
from ..storage.memory import get_lang
from .main_menu import build_main_menu

router = Router()

BTN_SET = {L["uz"]["btn_materials"], L["en"]["btn_materials"], L["ru"]["btn_materials"]}

@router.message(F.text.in_(BTN_SET))
async def materials_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    text = f"{t.get('materials_title','📚 Materiallar')}\n\n{t.get('materials_hint','')}"
    await message.answer(text, reply_markup=build_main_menu(lang))
