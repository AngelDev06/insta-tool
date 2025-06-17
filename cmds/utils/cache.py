import json
from termcolor import colored
from sys import stdout
from itertools import chain
from typing import TypedDict, Optional, Self, overload, Any, TextIO, Unpack
from pathlib import Path
from datetime import datetime
from .tool_logger import logger
from .user_info import UserInfo

CACHE_FOLDER = Path("user info")


class UpdateCacheType(TypedDict):
    added: list[str]
    removed: list[str]


class ChangelogCacheType(TypedDict):
    timestamp: float
    followers: UpdateCacheType
    followings: UpdateCacheType


class UserCacheType(TypedDict):
    followers: list[str]
    followings: list[str]
    changelog: list[ChangelogCacheType]


class _OutputUpdateKwargsType(TypedDict):
    new: set[str]
    removed: set[str]


# holds user information that comes from the cache (also includes changelog info)
class UserCache:
    def __init__(self, data: Optional[UserCacheType] = None) -> None:
        self._empty = False
        if data is None:
            data = {"followers": [], "followings": [], "changelog": []}
            self._empty = True
        self._data: UserCacheType = data

    def __bool__(self) -> bool:
        return not self._empty

    def analyse(self, reverse: bool) -> set[str]:
        followers, followings = set(self.followers), set(self.followings)
        if not reverse:
            return followings.difference(followers)
        return followers.difference(followings)

    def dump_update(
        self, info: UserInfo, out: Optional[TextIO] = None
    ) -> None:
        changelog: ChangelogCacheType = {
            "timestamp": datetime.now().timestamp(),
            "followers": {"added": [], "removed": []},
            "followings": {"added": [], "removed": []},
        }

        for list_name in ("followers", "followings"):
            cached_list: set[str] = set(self._data[list_name])
            new_list: set[str] = getattr(info, list_name)
            added = new_list.difference(cached_list)
            removed = cached_list.difference(new_list)

            if not added and not removed:
                if out is not None:
                    out.write(f"{list_name} list: no update\n")
                continue

            changelog[list_name]["added"] = list(added)
            changelog[list_name]["removed"] = list(removed)

            if out is not None:
                self._output_update(list_name, out, new=added, removed=removed)

        if info.follower_count != len(
            info.followers
        ) or info.following_count != len(info.followings):
            if (
                input(
                    "not all the requested users were fetched, should the result be cached regardless? (Y/n) "
                )
                != "Y"
            ):
                return

        self._data["followers"] = list(info.followers)
        self._data["followings"] = list(info.followings)
        self._data["changelog"].append(changelog)

        if not CACHE_FOLDER.is_dir():
            CACHE_FOLDER.mkdir()

        with open(
            CACHE_FOLDER / f"{info.username}.json", "w", encoding="utf-8"
        ) as file:
            json.dump(self._data, file, indent=2)

        logger.info("cached the result")

    @property
    def followers(self) -> list[str]:
        return self._data["followers"]

    @property
    def followings(self) -> list[str]:
        return self._data["followings"]

    @property
    def changelog(self) -> list[ChangelogCacheType]:
        return self._data["changelog"]

    def _output_update(
        self,
        list_name: str,
        out: TextIO,
        **kwargs: Unpack[_OutputUpdateKwargsType],
    ) -> None:
        if self._data["changelog"]:
            last_changelog = self._data["changelog"][-1]
            last_date = datetime.fromtimestamp(last_changelog["timestamp"])
            last_date_text = last_date.strftime("%A %d %B %Y, %I:%M%p")
            out.write(f"Account Update\nSince: {last_date_text}\n\n")

        out.write(f"{list_name} list:\n")

        def style(text: str, color: str) -> str:
            return (
                colored(text, color, attrs=("bold", "underline"))
                if out is stdout
                else text
            )
        
        for change_type, sign, color in (("new", "+", "green"), ("removed", "-", "red")):
            out.write(f"\t{change_type} {list_name}")
            for user in kwargs[change_type]:
                out.write("\n\t\t")
                out.write(style(f"{sign} {user}", color))
            out.write("\n")


class Cache:
    _instance: Optional[Self] = None
    _users: dict[str, UserCache]

    @overload
    def __new__(cls, username: str) -> UserCache: ...

    @overload
    def __new__(cls, username: None) -> Self: ...

    def __new__(cls, username=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._users = {}

        if username is None:
            return cls._instance
        return cls._instance[username]

    def __getitem__(self, username: str) -> UserCache:
        data = self._users.get(username)
        if data is not None:
            return data

        path = CACHE_FOLDER / f"{username}.json"
        if not path.is_file():
            return UserCache()

        with open(path, encoding="utf-8") as file:
            cache: UserCacheType = json.load(file)

        Cache.validate(username, cache)
        return self._users.setdefault(username, UserCache(cache))

    @staticmethod
    def validate(username: str, cache: Any) -> None:
        match cache:
            case {
                "followers": [*followers],
                "followings": [*followings],
                "changelog": [*logs],
            } if all(
                (
                    isinstance(item, str)
                    for item in chain(followers, followings)
                )
            ):
                for log in logs:
                    match log:
                        case {
                            "timestamp": float(),
                            "followers": {
                                "added": [*followers_added],
                                "removed": [*followers_removed],
                            },
                            "followings": {
                                "added": [*followings_added],
                                "removed": [*followings_removed],
                            },
                        } if all(
                            (
                                isinstance(item, str)
                                for item in chain(
                                    followers_added,
                                    followers_removed,
                                    followings_added,
                                    followings_removed,
                                )
                            )
                        ):
                            continue
                    break
                else:
                    return
            # older format
            case {"followers": [*followers], "followings": [*followings]} if (
                all(
                    (
                        isinstance(item, str)
                        for item in chain(followers, followings)
                    )
                )
            ):
                cache["changelog"] = []
                return

        logger.critical(
            (
                f"cache for user '{username}' is corrupted! "
                f"please delete the file '{CACHE_FOLDER}/{username}.json' and retry"
            )
        )
        raise RuntimeError("corrupted cache")
