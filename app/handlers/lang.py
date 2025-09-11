from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..locales import L
from ..keyboards.reply import make_main_menu
from ..storage.memory import set_lang


router = Router()


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    if lang not in L:
        lang = "uz"


    set_lang(callback.from_user.id, lang)
    t = L[lang]


    await callback.message.edit_text(t["chosen"]) # Inline xabarini yangilash
    await callback.message.answer(t["menu_title"], reply_markup=make_main_menu(lang))
    await callback.answer()
