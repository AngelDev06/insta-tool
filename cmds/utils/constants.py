from pathlib import Path
from typing import Iterable, Literal, TypeAlias

ListsType: TypeAlias = Literal["followers", "followings"]
ChangesType: TypeAlias = Literal["added", "removed", "renamed"]
DiffsType: TypeAlias = Literal["user1", "user2", "mutuals"]


CONFIG_FOLDER = Path("config")
CACHE_FOLDER = Path("user info")
SESSIONS_FOLDER = Path("sessions")
LISTS: Iterable[ListsType] = ("followers", "followings")
CHANGES: Iterable[ChangesType] = ("added", "removed", "renamed")
DIFFS: Iterable[DiffsType] = ("user1", "user2", "mutuals")
CHANGES_ATTRS = dict(zip(CHANGES, (("+ ", "green"), ("- ", "red"), ("", "light_cyan"))))
DATE_OUTPUT_FORMAT = "%d/%m/%Y %I:%M:%S%p"
