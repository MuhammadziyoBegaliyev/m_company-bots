
import os
import sqlite3
from typing import Optional, Dict, Any, List

DB_PATH = "app/data/bot.sqlite3"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _normalize_phone(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    digits = "".join(ch for ch in s if ch.isdigit())
    # har doim + bilan E.164 ko‘rinishda saqlaymiz
    return f"+{digits}" if digits else ""


class DB:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None

    # ---------------- Low-level ----------------
    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._init_schema()   # bog‘langanda bir marta migratsiya
        return self._conn

    # Backward compat: ba’zi joylarda self.conn ishlatilgan bo‘lishi mumkin
    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def exec(self, sql: str, params: tuple = ()) -> None:
        with self.connect():
            self.conn.execute(sql, params)

    def query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        cur = self.connect().execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def query_all(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        cur = self.connect().execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    # ---------------- Schema & migrations ----------------
    def _column_exists(self, table: str, column: str) -> bool:
        cur = self.connect().execute(f"PRAGMA table_info({table});")
        cols = [r[1] for r in cur.fetchall()]
        cur.close()
        return column in cols

    def _init_schema(self) -> None:
        # Asosiy jadval
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

        # Yetishmayotgan ustunlarni qo‘shamiz
        if not self._column_exists("users", "last_feature"):
            self.exec("ALTER TABLE users ADD COLUMN last_feature TEXT;")

        if not self._column_exists("users", "last_seen"):
            self.exec("ALTER TABLE users ADD COLUMN last_seen DATETIME;")

        # Indekslar
        self.exec("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);")
        self.exec("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        self.exec("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen);")

    # Backward-compatible public API
    def init(self) -> None:
        """Old kodlar chaqirsa ham ishlaydi (hech narsa qilmaydi, chunki connect() allaqachon _init_schema() qiladi)."""
        self.connect()

    # ---------------- Helpers ----------------
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
        last_feature: Optional[str] = None,
        touch_seen: bool = True,
    ) -> None:
        # insert bo‘sh yozuv
        self.exec("INSERT OR IGNORE INTO users (user_id) VALUES (?);", (user_id,))

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
        if last_feature is not None:
            sets.append("last_feature = ?"); vals.append(last_feature)
        if touch_seen:
            sets.append("last_seen = CURRENT_TIMESTAMP")

        if sets:
            sql = f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?"
            vals.append(user_id)
            self.exec(sql, tuple(vals))

    # shorthand setterlar
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

    def set_last_feature(self, user_id: int, feature: str) -> None:
        self.upsert_user(user_id, last_feature=feature)

    def touch_last_seen(self, user_id: int) -> None:
        self.upsert_user(user_id, touch_seen=True)

    def is_onboarded(self, user_id: int) -> bool:
        u = self.get_user(user_id)
        return bool(u.get("onboarded", 0))

    # ---------------- Queries for admin panel ----------------
    def get_all_users(self, offset: int = 0, limit: int = 100) -> List[dict]:
        """
        Foydalanuvchilarni yangi->eski (last_seen, bo‘lmasa created_at) tartibida qaytaradi.
        """
        rows = self.query_all(
            """
            SELECT user_id, username, name, phone, lang, onboarded,
                   last_feature, created_at, last_seen
            FROM users
            ORDER BY COALESCE(last_seen, created_at) DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        res: List[dict] = []
        for r in rows:
            res.append({
                "user_id": r["user_id"],
                "username": r["username"],
                "name": r["name"],
                "phone": r["phone"],
                "lang": r["lang"],
                "onboarded": bool(r["onboarded"]) if r["onboarded"] is not None else False,
                "last_feature": r["last_feature"],
                "created_at": r["created_at"],
                "last_seen": r["last_seen"],
            })
        return res

    def find_user_by_username(self, username: str) -> Optional[dict]:
        row = self.query_one(
            """
            SELECT user_id, username, name, phone, lang, onboarded, last_feature
            FROM users
            WHERE LOWER(username) = LOWER(?)
            """,
            (username,),
        )
        if not row:
            return None
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "name": row["name"],
            "phone": row["phone"],
            "lang": row["lang"],
            "onboarded": bool(row["onboarded"]) if row["onboarded"] is not None else False,
            "last_feature": row["last_feature"],
        }


# Global instansiya
db = DB()
db.init()  
