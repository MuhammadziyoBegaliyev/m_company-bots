# app/handlers/contact.py
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from ..locales import L
from ..storage.memory import get_lang

router = Router()

# Reply tugma nomlari (3 tilda)
CONTACT_BTNS = {L["uz"]["btn_contact"], L["en"]["btn_contact"], L["ru"]["btn_contact"]}

# Ofis koordinatalari (Yunusobod, Bog'ishamol ko'chasi — moslab qo'ysangiz bo'ladi)
OFFICE_LAT = 41.339893
OFFICE_LON = 69.293765


def _main_kb(lang: str) -> InlineKeyboardMarkup:
    t = L[lang]
    rows = [
        [
            InlineKeyboardButton(text=f"📍 {t['contact_addr_btn']}",  callback_data="contact:addr"),
            InlineKeyboardButton(text=f"✉️ {t['contact_email_btn']}", callback_data="contact:mail"),
        ],
        [
            InlineKeyboardButton(text=f"📞 {t['contact_call_btn']}",   callback_data="contact:call"),
            InlineKeyboardButton(text=f"🕒 {t['contact_hours_btn']}",  callback_data="contact:hours"),
        ],
        [InlineKeyboardButton(text=f"🌐 {t['contact_social_btn']}",   callback_data="contact:social")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _social_kb(lang: str) -> InlineKeyboardMarkup:
    t = L[lang]
    rows = [
        [
            InlineKeyboardButton(text="📣 Telegram", callback_data="social:tg"),
            InlineKeyboardButton(text="📸 Instagram", url="https://instagram.com/mcompanyuz"),
        ],
        [
            InlineKeyboardButton(text="📘 Facebook", url="https://mcompany.uz"),  # agar FB yo'q bo'lsa saytga
            InlineKeyboardButton(text="🌐 Website",  url="https://mcompany.uz"),
        ],
        [
            InlineKeyboardButton(text="🔗 Website #2", url="https://mcompany.uz"),
            InlineKeyboardButton(text="🏷️ Website #3", url="https://mcompany.uz"),
        ],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(CONTACT_BTNS))
async def contact_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L[lang]
    await message.answer(t["contact_title"], reply_markup=_main_kb(lang))


# --- 1) Ofis manzili ---
@router.callback_query(F.data == "contact:addr")
async def contact_addr(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()
    await cb.message.answer(f"📍 {t['contact_address_text']}")
    await cb.message.answer_location(latitude=OFFICE_LAT, longitude=OFFICE_LON)

    maps_url = f"https://yandex.uz/maps/10335/tashkent/?ll=69.296346%2C41.339445&mode=poi&poi%5Bpoint%5D=69.293765%2C41.339893&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D117349227100&z=18.31q={OFFICE_LAT},{OFFICE_LON}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["open_in_maps_btn"], url=maps_url)],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])
    await cb.message.answer(t["contact_more_opts"], reply_markup=kb)


# --- 2) Pochta orqali yozish ---
@router.callback_query(F.data == "contact:mail")
async def contact_mail(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()

    # http/https URL talab qilinadi — Gmail compose havolasidan foydalanamiz
    gmail_url = "https://mail.google.com/mail/?view=cm&to=info@mcompany.uz"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t.get("open_in_gmail_btn", "📨 Open in Gmail"), url=gmail_url)],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])
    await cb.message.answer(f"✉️ {t['contact_email_text']}", reply_markup=kb)


# --- 3) To'g'ridan-to'g'ri bog'lanish ---
@router.callback_query(F.data == "contact:call")
async def contact_call(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()

    # tel: URL ishlamaydi. Buning o'rniga contact card jo'natamiz — Telegram o'zi “Call” tugmasini beradi.
    # send_contact ga reply_markup ham biriktirish mumkin.
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])
    await cb.message.answer_contact(
        phone_number="+998908086383",
        first_name="M Company",
        reply_markup=kb
    )
    # Qo'shimcha matn (ixtiyoriy)
    await cb.message.answer(f"📞 {t['contact_phone_text']}")


# --- 4) Ish vaqtlari ---
@router.callback_query(F.data == "contact:hours")
async def contact_hours(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")]
    ])
    await cb.message.answer(f"🕒 {t['contact_hours_text']}", reply_markup=kb)


# --- 5) Ijtimoiy tarmoqlar ---
@router.callback_query(F.data == "contact:social")
async def contact_social(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()
    await cb.message.answer(f"🌐 {t['contact_social_title']}", reply_markup=_social_kb(lang))


@router.callback_query(F.data == "contact:back")
async def contact_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()
    await cb.message.answer(t["contact_title"], reply_markup=_main_kb(lang))


# --- Social: Telegram tugmasi bosilganda matn + link ---
@router.callback_query(F.data == "social:tg")
async def social_tg(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = L[lang]
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📣 @Narkuziyev", url="https://t.me/Narkuziyev")],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])
    await cb.message.answer(t["contact_tg_text"], reply_markup=kb)
