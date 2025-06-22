import json
from itertools import chain
from typing import (
    TypedDict,
    Optional,
    Self,
    overload,
    Any,
    Protocol,
    Literal,
    TypeAlias,
    Iterable,
)
from pathlib import Path
from datetime import datetime, date
from dataclasses import dataclass, field

from .tool_logger import logger
from .user_info import UserInfo

CACHE_FOLDER = Path("user info")

ListsType: TypeAlias = Literal["followers", "followings"]
ChangesType: TypeAlias = Literal["added", "removed"]


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


class OutputUpdateCallback(Protocol):
    def __call__(self, list_name: ListsType, **kwargs: set[str]) -> None:
        pass


# user status at a specific point in time (resulted from backtracing cached records)
@dataclass
class UserLists:
    followers: set[str] = field(default_factory=set)
    followings: set[str] = field(default_factory=set)

    def diff(self, reverse: bool) -> set[str]:
        if not reverse:
            return self.followings - self.followers
        return self.followers - self.followings

    def __sub__(self, other: Self):
        return UserLists(
            followers=self.followers - other.followers,
            followings=self.followings - other.followings,
        )

    def __and__(self, other: Self):
        return UserLists(
            followers=self.followers & other.followers,
            followings=self.followings & other.followings,
        )


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

    def checkout(
        self,
        at: date,
        lists: Iterable[ListsType] = ("followers", "followings"),
    ) -> UserLists:
        list_table = {
            list_name: set(getattr(self, list_name)) for list_name in lists
        }

        for log in reversed(self.changelog):
            log_date = date.fromtimestamp(log["timestamp"])
            if log_date <= at:
                break

            for list_name in lists:
                list_table[list_name] -= set(log[list_name]["added"])
                list_table[list_name] |= set(log[list_name]["removed"])

        return UserLists(**list_table)

    def dump_update(
        self, info: UserInfo, callback: Optional[OutputUpdateCallback] = None
    ) -> None:
        changelog: ChangelogCacheType = {
            "timestamp": datetime.now().timestamp(),
            "followers": {"added": [], "removed": []},
            "followings": {"added": [], "removed": []},
        }

        for list_name in ("followers", "followings"):
            cached_list: set[str] = set(self._data[list_name])
            new_list: set[str] = getattr(info, list_name)
            added = new_list - cached_list
            removed = cached_list - new_list

            changelog[list_name]["added"] = list(added)
            changelog[list_name]["removed"] = list(removed)

            if callback is not None:
                callback(list_name, added=added, removed=removed)

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

    @property
    def lists(self) -> UserLists:
        return UserLists(set(self.followers), set(self.followings))


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
