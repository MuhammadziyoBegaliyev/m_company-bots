
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.exceptions import TelegramBadRequest

from ..locales import L
from ..storage.memory import get_lang

router = Router()

# === Config: Office koordinatalari ===
OFFICE_LAT = 41.339893
OFFICE_LON = 69.293765

# === Reply tugmalari (uch tilda) ===
CONTACT_BTNS = {
    L["uz"]["btn_contact"],
    L["en"]["btn_contact"],
    L["ru"]["btn_contact"],
}

# ---------- Helpers ----------
def _t(lang: str) -> dict:
    """Til lug‘ati (Uzbek fallback)."""
    return L.get(lang, L["uz"])

def _main_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
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
    t = _t(lang)
    rows = [
        [
            InlineKeyboardButton(text="📣 Telegram", callback_data="social:tg"),
            InlineKeyboardButton(text="📸 Instagram", url="https://instagram.com/mcompanyuz"),
        ],
        [
            InlineKeyboardButton(text="📘 Facebook", url="https://mcompany.uz"),
            InlineKeyboardButton(text="🌐 Website",  url="https://mcompany.uz"),
        ],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def _safe_cb_answer(cb: CallbackQuery, *args, **kwargs):
    """‘query is too old’ xatolarini yutib yuborish uchun xavfsiz cb.answer()."""
    try:
        await cb.answer(*args, **kwargs)
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "query is too old" in s or "query id is invalid" in s:
            return
        raise



# ---------- Entry: Reply tugmadan ----------
@router.message(F.text.in_(CONTACT_BTNS))
async def contact_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(t["contact_title"], reply_markup=_main_kb(lang))


# ---------- Entry: Welcome inline tugmadan ----------
@router.callback_query(F.data == "nav:contact")
async def nav_contact(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    await _safe_cb_answer(cb)
    t = _t(lang)
    await cb.message.answer(t["contact_title"], reply_markup=_main_kb(lang))


# ---------- Address ----------
@router.callback_query(F.data == "contact:addr")
async def contact_addr(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    await _safe_cb_answer(cb)

    title = t.get("contact_addr_title") or "M Company Office"
    address = t["contact_address_text"]

    maps_url = f"https://maps.google.com/?q={OFFICE_LAT},{OFFICE_LON}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["open_in_maps_btn"], url=maps_url)],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])

    # 1 ta xabar: joylashuv (venue) + pastida inline tugmalar
    try:
        await cb.message.answer_venue(
            latitude=OFFICE_LAT,
            longitude=OFFICE_LON,
            title=title,
            address=address,
            reply_markup=kb
        )
    except AttributeError:
        # Aiogram versiyasida answer_venue yo‘q bo‘lsa
        await cb.message.bot.send_venue(
            chat_id=cb.message.chat.id,
            latitude=OFFICE_LAT,
            longitude=OFFICE_LON,
            title=title,
            address=address,
            reply_markup=kb
        )


# ---------- Email ----------
@router.callback_query(F.data == "contact:mail")
async def contact_mail(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await _safe_cb_answer(cb)

    gmail_url = "https://mail.google.com/mail/?view=cm&to=info@mcompany.uz"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t.get("open_in_gmail_btn", "📨 Open in Gmail"), url=gmail_url)],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])
    await cb.message.answer(f"✉️ {t['contact_email_text']}", reply_markup=kb)


# ---------- Call (to‘g‘ridan-to‘g‘ri) ----------
@router.callback_query(F.data == "contact:call")
async def contact_call(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    await _safe_cb_answer(cb)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Telegram", url="https://t.me/Narkuziyev")],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])

    # Bitta xabar ichida: contact card + inline tugmalar
    await cb.message.answer_contact(
        phone_number="+998908086383",
        first_name="M Company",
        vcard="BEGIN:VCARD\nVERSION:3.0\nFN:M Company\nTEL;TYPE=CELL:+998908086383\nEND:VCARD",
        reply_markup=kb
    )


# ---------- Working hours ----------
@router.callback_query(F.data == "contact:hours")
async def contact_hours(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await _safe_cb_answer(cb)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")]
    ])
    await cb.message.answer(f"🕒 {t['contact_hours_text']}", reply_markup=kb)


# ---------- Social ----------
@router.callback_query(F.data == "contact:social")
async def contact_social(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await _safe_cb_answer(cb)
    await cb.message.answer(f"🌐 {t['contact_social_title']}", reply_markup=_social_kb(lang))

@router.callback_query(F.data == "social:tg")
async def social_tg(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await _safe_cb_answer(cb)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📣 @Narkuziyev", url="https://t.me/Narkuziyev")],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="contact:back")],
    ])
    await cb.message.answer(t["contact_tg_text"], reply_markup=kb)


# ---------- Back to Contact main ----------
@router.callback_query(F.data == "contact:back")
async def contact_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await _safe_cb_answer(cb)
    await cb.message.answer(t["contact_title"], reply_markup=_main_kb(lang))
