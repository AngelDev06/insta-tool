from typing import TypeAlias, Literal
from pathlib import Path

CONFIG_PATH = Path("config")
CACHE_FOLDER = Path("user info")
SESSIONS_FOLDER = Path("sessions")
LISTS = ("followers", "followings")
CHANGES = ("added", "removed", "renamed")
DIFFS = ("user1", "user2", "mutuals")
CHANGES_ATTRS = dict(
    zip(CHANGES, (("+ ", "green"), ("- ", "red"), ("", "light_cyan")))
)
DATE_OUTPUT_FORMAT = "%d/%m/%Y %I:%M:%S%p"

ListsType: TypeAlias = Literal["followers", "followings"]
ChangesType: TypeAlias = Literal["added", "removed", "renamed"]
DiffsType: TypeAlias = Literal["user1", "user2", "mutuals"]
