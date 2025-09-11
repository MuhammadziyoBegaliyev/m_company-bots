from typing import Dict


_user_lang: Dict[int, str] = {}


def get_lang(user_id: int, default: str = "uz") -> str:
    return _user_lang.get(user_id, default)




def set_lang(user_id: int, lang: str) -> None:
    _user_lang[user_id] = lang