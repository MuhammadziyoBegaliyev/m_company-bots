# -*- coding: utf-8 -*-
# app/storage/memory.py

from typing import Dict, Optional

# --- Til xotirasi (in-memory) ---
_LANGS: Dict[int, str] = {}


def set_lang(user_id: int, lang: str) -> None:
    _LANGS[user_id] = lang


def get_lang(user_id: int, default: str = "uz") -> str:
    return _LANGS.get(user_id, default)


# --- Telefon xotirasi (in-memory) ---
_PHONES: Dict[int, str] = {}


def _normalize_phone(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    return f"+{digits}" if plus else digits


def set_phone(user_id: int, phone: str) -> None:
    phone = _normalize_phone(phone)
    if phone:
        _PHONES[user_id] = phone


def get_phone(user_id: int, default: Optional[str] = None) -> Optional[str]:
    return _PHONES.get(user_id, default)
