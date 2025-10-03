# -*- coding: utf-8 -*-
# app/storage/db.py

import os
import sqlite3
from typing import Optional, Dict, Any

DB_PATH = "app/data/bot.sqlite3"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _normalize_phone(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    return f"+{digits}" if plus else digits


class DB:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None

    # --- low level ---
    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def exec(self, sql: str, params: tuple = ()) -> None:
        conn = self.connect()
        with conn:
            conn.execute(sql, params)

    def query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        cur = self.connect().execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    # --- schema ---
    def init(self) -> None:
        self.exec(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER UNIQUE NOT NULL,
                username    TEXT,
                name        TEXT,
                phone       TEXT,
                lang        TEXT,
                onboarded   INTEGER DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    # --- helpers ---
    def get_user(self, user_id: int) -> Dict[str, Any]:
        row = self.query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(row) if row else {}

    def upsert_user(
        self,
        user_id: int,
        *,
        username: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        lang: Optional[str] = None,
        onboarded: Optional[bool] = None,
    ) -> None:
        # insert stub if not exists
        self.exec(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?);",
            (user_id,),
        )
        # patch
        sets, vals = [], []
        if username is not None:
            sets.append("username = ?"); vals.append(username)
        if name is not None:
            sets.append("name = ?"); vals.append(name)
        if phone is not None:
            sets.append("phone = ?"); vals.append(_normalize_phone(phone))
        if lang is not None:
            sets.append("lang = ?"); vals.append(lang)
        if onboarded is not None:
            sets.append("onboarded = ?"); vals.append(1 if onboarded else 0)
        if sets:
            sql = f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?"
            vals.append(user_id)
            self.exec(sql, tuple(vals))

    def set_lang(self, user_id: int, lang: str) -> None:
        self.upsert_user(user_id, lang=lang)

    def set_name(self, user_id: int, name: str) -> None:
        self.upsert_user(user_id, name=name)

    def set_phone(self, user_id: int, phone: str) -> None:
        self.upsert_user(user_id, phone=phone)

    def set_username(self, user_id: int, username: Optional[str]) -> None:
        self.upsert_user(user_id, username=username or None)

    def set_onboarded(self, user_id: int, value: bool = True) -> None:
        self.upsert_user(user_id, onboarded=value)

    def is_onboarded(self, user_id: int) -> bool:
        u = self.get_user(user_id)
        return bool(u.get("onboarded", 0))



     def get_all_users(self, offset: int = 0, limit: int = 100) -> list[dict]:
        """
        Foydalanuvchilarni yangi->eski tartibda qaytaradi.
        user_id, username, name, phone, lang, onboarded, last_feature, created_at, last_seen kabi maydonlar bo‘lishi ma‘qul.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT user_id, username, name, phone, lang, onboarded, last_feature, created_at, last_seen
            FROM users
            ORDER BY COALESCE(last_seen, created_at) DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cur.fetchall()
        res = []
        for r in rows:
            res.append({
                "user_id": r[0],
                "username": r[1],
                "name": r[2],
                "phone": r[3],
                "lang": r[4],
                "onboarded": bool(r[5]) if r[5] is not None else False,
                "last_feature": r[6],
                "created_at": r[7],
                "last_seen": r[8],
            })
        return res

    def find_user_by_username(self, username: str) -> dict | None:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT user_id, username, name, phone, lang, onboarded, last_feature
            FROM users WHERE LOWER(username)=LOWER(?)
        """, (username,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "user_id": r[0],
            "username": r[1],
            "name": r[2],
            "phone": r[3],
            "lang": r[4],
            "onboarded": bool(r[5]) if r[5] is not None else False,
            "last_feature": r[6],
        }

db = DB()
