from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from ..locales import L
from ..keyboards.inline import LANG_KB


router = Router()


@router.message(CommandStart())
async def start(message: Message):
    name = message.from_user.full_name or message.from_user.first_name or ""


    # 3 tilda salom
    greet_uz = f"Assalomu alaykum hurmatli {name}"
    greet_en = f"Hello {name}"
    greet_ru = f"Привет {name}"


    text = (
    f"{greet_uz}\n{greet_en}\n{greet_ru}\n\n" # kirishda talabbingiz bo'yicha 3 tilda salom
    + L["uz"]["greet_prompt"]
    )
    await message.answer(text, reply_markup=LANG_KB)