from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from .constants import CACHE_FOLDER

UIDS_PATH = CACHE_FOLDER / "uids.json"
_uid_map: Optional[UIDMap] = None


class UIDMap(BaseModel):
    table: dict[str, int] = Field(default_factory=dict)

    @classmethod
    def get(cls):
        global _uid_map
        if _uid_map is not None:
            return _uid_map
        if not UIDS_PATH.is_file():
            _uid_map = cls()
        else:
            with open(UIDS_PATH, encoding="utf-8") as file:
                _uid_map = cls.model_validate_json(file.read())
        return _uid_map

    def backup(self):
        if not CACHE_FOLDER.is_dir():
            CACHE_FOLDER.mkdir()
        with open(UIDS_PATH, "w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=2))

    def add_entry(self, username: str, uid: int, backup: bool = True):
        self.table[username] = uid
        if backup:
            self.backup()

    def uid_of(self, username: str):
        return self.table.get(username)
