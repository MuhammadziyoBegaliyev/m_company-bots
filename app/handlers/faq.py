
from __future__ import annotations

from typing import Dict, List, Tuple
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from ..locales import L
from ..storage.memory import get_lang, get_phone
from ..config import settings

router = Router()

# --- ENV: ADMIN_IDS (list[int]) ---
ADMIN_IDS: List[int] = list(getattr(settings, "admin_ids", []) or [])

# --- ENV: FAQ_GROUP_IDS (list[int]) yoki bitta faq_group_id ---
FAQ_GROUP_IDS: List[int] = list(getattr(settings, "faq_group_ids", []) or [])
if not FAQ_GROUP_IDS:
    single = getattr(settings, "faq_group_id", None)
    if single:
        FAQ_GROUP_IDS = [int(single)]

# --- Savollar kalitlari ---
FAQ_KEYS = ["q1", "q2", "q3", "q4", "q5", "q6", "q7"]

# Reply tugma matnlari (3 tilda)
FAQ_BTNS = {L["uz"]["btn_faq"], L["en"]["btn_faq"], L["ru"]["btn_faq"]}

# --- Holatlar ---
class AskQuestion(StatesGroup):
    waiting_text = State()

# --- Guruhga yuborilgan savol bilan foydalanuvchini bog‘lash (guruh_id, msg_id) -> user_info ---
# Eslatma: Bu xotira ichida saqlanadi (process qayta ishga tushsa yo‘qoladi).
QUESTION_LINK: Dict[Tuple[int, int], Dict[str, str | int]] = {}


def _faq_keyboard(lang: str) -> InlineKeyboardMarkup:
    """7 ta savol + 'Savol berish' + Orqaga."""
    t = L[lang]

    def q(text: str) -> str:
        return f"❓ {text}"

    buttons = [
        InlineKeyboardButton(text=q(t["faq_q1"]), callback_data="faq:q1"),
        InlineKeyboardButton(text=q(t["faq_q2"]), callback_data="faq:q2"),
        InlineKeyboardButton(text=q(t["faq_q3"]), callback_data="faq:q3"),
        InlineKeyboardButton(text=q(t["faq_q4"]), callback_data="faq:q4"),
        InlineKeyboardButton(text=q(t["faq_q5"]), callback_data="faq:q5"),
        InlineKeyboardButton(text=q(t["faq_q6"]), callback_data="faq:q6"),
        InlineKeyboardButton(text=q(t["faq_q7"]), callback_data="faq:q7"),
        InlineKeyboardButton(text=f"✉️ {t['faq_btn_ask']}", callback_data="faq:ask"),
        InlineKeyboardButton(text=t["back_btn"], callback_data="faq:back"),
    ]
    rows = [
        [buttons[0]],
        [buttons[1]],
        [buttons[2]],
        [buttons[3]],
        [buttons[4]],
        [buttons[5]],
        [buttons[6]],
        [buttons[7]],
        [buttons[8]],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _back_kb(lang: str) -> InlineKeyboardMarkup:
    t = L[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t["back_btn"], callback_data="faq:back")]]
    )


@router.message(F.text.in_(FAQ_BTNS))
async def faq_entry(message: Message):
    """FAQ bo'limini ko'rsatish."""
    lang = get_lang(message.from_user.id, "uz")
    t = L[lang]
    await message.answer(t["faq_title"], reply_markup=_faq_keyboard(lang))


@router.callback_query(F.data == "faq:back")
async def faq_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L[lang]
    await cb.answer()
    await cb.message.answer(t["faq_title"], reply_markup=_faq_keyboard(lang))


# --- Savollarga javob beruvchi handler ---
@router.callback_query(F.data.startswith("faq:q"))
async def faq_answer(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L[lang]
    key = cb.data.split(":", 1)[1]  # q1..q7
    ans_key = f"faq_a{key[1:]}"     # a1..a7
    answer = t.get(ans_key, t["stub"])
    await cb.answer()
    await cb.message.answer(answer, reply_markup=_back_kb(lang))


# --- Savol berish oqimi (foydalanuvchidan matn) ---
@router.callback_query(F.data == "faq:ask")
async def faq_ask_start(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz")
    t = L[lang]
    await cb.answer()
    await state.set_state(AskQuestion.waiting_text)
    await cb.message.answer(
        f"✉️ {t['faq_ask_prompt']}",
        reply_markup=_back_kb(lang)
    )


@router.message(AskQuestion.waiting_text)
async def faq_receive_question(message: Message, state: FSMContext):
    """Foydalanuvchi savolini qabul qiladi va M Company guruh(lar)i ga yuboradi.
    Guruhda admin(lar) shu xabarga REPLY qilib javob yozsa, bot javobni foydalanuvchiga yuboradi.
    """
    lang = get_lang(message.from_user.id, "uz")
    t = L[lang]

    text = (message.text or "").strip()
    if not text:
        await message.answer(f"✉️ {t['faq_ask_prompt']}")
        return

    # Foydalanuvchi ma'lumotlari
    u = message.from_user
    display = u.full_name or u.first_name or "User"
    uname = f"@{u.username}" if u.username else "—"
    phone = get_phone(u.id , default="None")
    if not FAQ_GROUP_IDS:
        await message.answer("⚠️ FAQ guruhi sozlanmagan. Administratorga murojaat qiling.")
        await state.clear()
        return

    # Guruh(lar)ga yuboriladigan xabar matni
    payload = (
        "🆕 <b>Yangi savol</b>\n"
        f"👤 <b>User</b>: {display} ({uname}, id=<code>{u.id}</code>)\n"
        f"🌐 <b>Lang</b>: {lang}\n\n"
        f"📞 <b>Phone</b>: {phone}\n\n" 
        f"❓ <b>Question</b>:\n{text}\n\n"
        "ℹ️ <i>Javob berish uchun shu xabarga <b>reply</b> yozing — foydalanuvchiga DM sifatida yuboriladi.</i>"
    )

    sent_something = False
    for gid in FAQ_GROUP_IDS:
        try:
            sent = await message.bot.send_message(
                chat_id=gid,
                text=payload,
                parse_mode="HTML"
            )
            # Bog'lash: (guruh_id, guruh_msg_id) -> foydalanuvchi
            QUESTION_LINK[(sent.chat.id, sent.message_id)] = {
                "user_id": u.id,
                "first_name": u.first_name or display,
                "lang": lang,
            }
            sent_something = True
        except Exception as e:
            # Guruhga yuborib bo'lmadi (bot a'zo emas / chat not found / bloklangan)
            await message.answer(f"⚠️ Guruh {gid} ga yuborilmadi: {e}")

    if sent_something:
        await message.answer(f"✅ {t['faq_ask_received']}")
    else:
        await message.answer("❗️ Savolni guruhga yuborib bo‘lmadi. Keyinroq urinib ko‘ring.")

    await state.clear()


# --- Guruhda admin reply yozsa — foydalanuvchiga yuborish ---
@router.message(
    F.chat.type.in_({"supergroup", "group"}) &
    F.reply_to_message
)
async def group_reply_router(message: Message):
    """Faqat belgilangan M Company guruh(lar)i ichida ishlaydi."""
    if message.chat.id not in FAQ_GROUP_IDS:
        return

    ref = message.reply_to_message
    if not ref:
        return

    # Faqat bot yuborgan savollarga bog'langan xabarlarga javob
    if not ref.from_user or not ref.from_user.is_bot:
        return

    key = (message.chat.id, ref.message_id)
    link = QUESTION_LINK.get(key)
    if not link:
        return  # Bu reply biz bog'lagan savolga tegishli emas

    user_id = int(link["user_id"])
    first_name = str(link.get("first_name", ""))
    # Javob matni (matn yoki media caption)
    body = (message.text or message.caption or "").strip()

    if not body:
        # Matnsiz javob — foydalanuvchiga hech bo'lmaganda bildirishnoma
        try:
            await message.bot.send_message(
                chat_id=user_id,
                text=f"{first_name},\nℹ️ Sizga javob yuborildi (media/forward)."
            )
        except Exception:
            pass
    else:
        try:
            await message.bot.send_message(
                chat_id=user_id,
                text=f"Assalomu aleykum hurmatli {first_name},\n✅Javob:{body}"
            )
        except Exception as e:
            await message.reply(f"❌ Foydalanuvchiga yuborib bo‘lmadi: {e}")
            return

    # Adminni xabardor qilamiz
    try:
        await message.reply("✅ Javob foydalanuvchiga yuborildi.")
    except Exception:
        pass


# --- Qo'shimcha: Guruh ID topish uchun /id ---
@router.message(Command("id"))
async def chat_id_echo(message: Message):
    await message.reply(
        f"Chat: <b>{message.chat.title or message.chat.type}</b>\nID: <code>{message.chat.id}</code>",
        parse_mode="HTML"
    )
