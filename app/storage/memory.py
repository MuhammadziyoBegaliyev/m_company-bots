# -*- coding: utf-8 -*-
# app/storage/memory.py
"""
In-memory soddalashtirilgan kesh.
Asosiy saqlash — app/storage/db.py dagi SQLite (bo‘lsa). Bo‘lmasa ham ishlaydi.
"""

from typing import Dict, Optional

# Ixtiyoriy DB: bor-bo‘lmasin yiqilmasin
try:
    from .db import db  # kutilyotgan API: get_user, set_lang, set_phone, upsert_user, is_onboarded, set_onboarded
except Exception:
    class _DummyDB:
        def get_user(self, user_id: int) -> dict: return {}
        def set_lang(self, user_id: int, lang: str) -> None: ...
        def set_phone(self, user_id: int, phone: str) -> None: ...
        def upsert_user(self, user_id: int, **kwargs) -> None: ...
        def is_onboarded(self, user_id: int) -> bool: return False
        def set_onboarded(self, user_id: int, value: bool = True) -> None: ...
    db = _DummyDB()

# --- Til kesh (ixtiyoriy) ---
_LANGS: Dict[int, str] = {}

def set_lang(user_id: int, lang: str) -> None:
    _LANGS[user_id] = lang
    try:
        db.set_lang(user_id, lang)
    except Exception:
        pass

def get_lang(user_id: int, default: str = "uz") -> str:
    try:
        return _LANGS.get(user_id) or db.get_user(user_id).get("lang") or default
    except Exception:
        return _LANGS.get(user_id, default)

# --- Telefon (kesh) ---
_PHONES: Dict[int, str] = {}

def set_phone(user_id: int, phone: str) -> None:
    if phone:
        _PHONES[user_id] = phone
        try:
            db.set_phone(user_id, phone)
        except Exception:
            pass

def get_phone(user_id: int, default: Optional[str] = None) -> Optional[str]:
    try:
        return _PHONES.get(user_id) or db.get_user(user_id).get("phone") or default
    except Exception:
        return _PHONES.get(user_id, default)

# --- Profil API (DB-ustidan yupqa o‘rama) ---
_ALLOWED_DB_FIELDS = {"name", "phone", "username", "onboarded", "lang"}

def get_profile(user_id: int) -> dict:
    try:
        return db.get_user(user_id) or {}
    except Exception:
        return {}

def set_profile(user_id: int, **kwargs) -> None:
    # DB’ga faqat tanlangan maydonlarni yuboramiz (aks holda upsert_user xafa bo‘ladi)
    payload = {k: v for k, v in kwargs.items() if k in _ALLOWED_DB_FIELDS}
    if not payload:
        return
    try:
        db.upsert_user(user_id, **payload)
    except Exception:
        pass

def is_onboarded(user_id: int) -> bool:
    try:
        return bool(db.is_onboarded(user_id))
    except Exception:
        return False

def set_onboarded(user_id: int, value: bool = True) -> None:
    try:
        db.set_onboarded(user_id, value)
    except Exception:
        pass
