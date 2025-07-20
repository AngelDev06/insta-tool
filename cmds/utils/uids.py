import json
from .constants import CACHE_FOLDER

UIDS_PATH = CACHE_FOLDER / "uids.json"
_uid_table: dict[str, int] = {}

def get_uid_table() -> dict[str, int]:
    global _uid_table
    if _uid_table:
        return _uid_table
    if not UIDS_PATH.is_file():
        return _uid_table
    with open(UIDS_PATH, encoding="utf-8") as file:
        _uid_table = json.load(file)
    return _uid_table

def store_uid(username: str, uid: int):
    if username in _uid_table:
        return
    _uid_table[username] = uid
    
    with open(UIDS_PATH, "w", encoding="utf-8") as file:
        json.dump(_uid_table, file, indent=2)
