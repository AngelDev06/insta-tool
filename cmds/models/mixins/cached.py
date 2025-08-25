from typing import Any, ClassVar, Self

from ...utils.constants import CACHE_FOLDER
from ...utils.tool_logger import logger
from ...utils.uids import UIDMap

_cached: dict[tuple[str, int], Any] = {}


class Cached:
    subdir: ClassVar[str] = ""

    @classmethod
    def get(cls, username: str) -> Self:
        key = (username, id(cls))
        if key in _cached:
            return _cached[key]
        uid = UIDMap.get().uid_of(username)
        if uid is None:
            return _cached.setdefault(key, cls())

        path = CACHE_FOLDER / cls.subdir / f"{uid}.json"
        if not path.is_file():
            return _cached.setdefault(key, cls())

        with open(path, encoding="utf-8") as file:
            return _cached.setdefault(key, cls.model_validate_json(file.read()))

    def dump(self, username: str, uid: int):
        target_dir = CACHE_FOLDER / self.__class__.subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / f"{uid}.json", "w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=2))

        UIDMap.get().add_entry(username, uid)
        logger.info("cached the result")
