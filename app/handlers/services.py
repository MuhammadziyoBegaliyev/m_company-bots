# app/handlers/services.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ..locales import L
from ..storage.memory import get_lang

router = Router()

# Reply tugma matnlari
SERVICES_BTNS = {L["uz"]["btn_services"], L["en"]["btn_services"], L["ru"]["btn_services"]}

# 6 ta xizmat kaliti (callback_data dagi qismlar)
SERVICE_KEYS = ["crm", "site", "leads", "arch", "ads", "call"]

ICONS = {
    "crm": "🤖",
    "site": "🕸️",
    "leads": "🎯",
    "arch": "🏗️",
    "ads": "📢",
    "call": "📞",
}

DETAIL_URLS = {
    "crm": "https://mcompany.uz/crm/",
    "site": "https://mcompany.uz/website/",
    "leads": "https://mcompany.uz/client/",
    "arch": "https://mcompany.uz/audit/starter/",
    "ads": "https://mcompany.uz/#res3",
    "call": "https://mcompany.uz/callCenter/",
}


def _services_menu_kb(lang: str) -> InlineKeyboardMarkup:
    """Xizmatlar ro‘yxati: 3 qatorda 2 tadan tugma."""
    t = L.get(lang, L["uz"])
    titles = [
        t["svc_crm"], t["svc_site"], t["svc_leads"],
        t["svc_arch"], t["svc_ads"], t["svc_call"],
    ]
    btns = [
        InlineKeyboardButton(
            text=f"{ICONS[k]} {title}",
            callback_data=f"svc:{k}",
        )
        for k, title in zip(SERVICE_KEYS, titles)
    ]
    rows = [[btns[i], btns[i+1]] for i in range(0, len(btns), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _detail_kb(lang: str, key: str) -> InlineKeyboardMarkup:
    """Bitta xizmat sahifasi uchun: (Batafsil) + (Orqaga)"""
    t = L.get(lang, L["uz"])
    rows = [
        [InlineKeyboardButton(text=t["svc_more"], url=DETAIL_URLS[key])],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="svc:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_(SERVICES_BTNS))
async def services_entry(message: Message):
    """Reply 'Xizmatlar' bosilganda intro + menyu chiqadi."""
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await message.answer(t["services_intro"], reply_markup=_services_menu_kb(lang))


@router.callback_query(F.data == "svc:back")
async def services_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await cb.answer()
    await cb.message.answer(t["services_intro"], reply_markup=_services_menu_kb(lang))


@router.callback_query(F.data.startswith("svc:"))
async def service_detail(cb: CallbackQuery):
    """Har bir xizmat tugmasi bosilganda batafsil matn + link tugmasi."""
    key = cb.data.split(":", 1)[1]
    if key not in SERVICE_KEYS:
        await cb.answer("...")
        return

    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    # Suzuvchi (popup) qisqa sarlavha
    await cb.answer(f"{ICONS[key]} {t.get(f'svc_{key}', key)}")

    # Matn + 'Batafsil' havolasi
    body = t.get(f"svc_{key}_body", t["stub"])
    await cb.message.answer(body, reply_markup=_detail_kb(lang, key))
