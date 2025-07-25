from __future__ import annotations
from copy import deepcopy
from datetime import datetime, date
from typing import Protocol, Optional, Iterable, Self
from pydantic import BaseModel, field_serializer, Field
from .fetched_user import FetchedUser
from .user import BasicUser
from .update import BasicUpdate, BasicUserUpdate, Update
from ..tool_logger import logger
from ..constants import ListsType, LISTS, CHANGES, CACHE_FOLDER
from ..uids import UIDMap

_cached_users: dict[str, CachedUser] = {}


class OutputUpdateCallback(Protocol):
    def __call__(self, list_name: ListsType, update: BasicUpdate) -> None: ...


class CachedUpdate(BasicUpdate, BaseModel):
    added: dict[int, str] = Field(default_factory=dict)
    removed: dict[int, str] = Field(default_factory=dict)
    renamed: dict[int, tuple[str, str]] = Field(default_factory=dict)


class CachedChangelogEntry(BasicUserUpdate, BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    followers: CachedUpdate = Field(default_factory=CachedUpdate)  # type: ignore[override]
    followings: CachedUpdate = Field(default_factory=CachedUpdate)  # type: ignore[override]

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime, _info):
        return timestamp.timestamp()


class CachedUser(BasicUser, BaseModel):
    followers: dict[int, str] = Field(default_factory=dict)
    followings: dict[int, str] = Field(default_factory=dict)
    changelog: list[CachedChangelogEntry] = Field(default_factory=list)

    @classmethod
    def get(cls, username: str) -> "CachedUser":
        if username in _cached_users:
            return _cached_users[username]
        
        uid = UIDMap.get().uid_of(username)
        if uid is None:
            return _cached_users.setdefault(username, cls())

        path = CACHE_FOLDER / f"{uid}.json"
        if not path.is_file():
            return _cached_users.setdefault(username, cls())

        with open(path, encoding="utf-8") as file:
            return _cached_users.setdefault(
                username, CachedUser.model_validate_json(file.read())
            )

    def is_empty(self) -> bool:
        return not bool(self.followers or self.followings or self.changelog)

    def __bool__(self) -> bool:
        return not self.is_empty()

    def checkout(self, at: date, lists: Iterable[ListsType] = LISTS) -> Self:
        """Backtraces up to a specific point in time (specified by `at`) and
        recovers the state of followers/followings

        Args:
            at (date): The point to which history will be recovered,
                note that the result will include any updates that happened
                during that day
            lists (Iterable[Literal["followers", "followings"]]): The lists to recover,
                defaults to both followers and followings
        Returns:
            A new `CachedUser` instance containing the state at the point in time specified"""
        kwargs: dict[str, dict[int, str]] = {
            list_name: getattr(self, list_name).copy() for list_name in lists
        }
        changelog_count: int = len(self.changelog)

        for log in reversed(self.changelog):
            if log.timestamp.date() <= at:
                break

            for list_name in lists:
                update: CachedUpdate = getattr(log, list_name)
                state: dict[int, str] = kwargs[list_name]

                for uid in list(update.added.keys()):
                    del state[uid]

                state |= update.removed

                for uid, (old_name, _) in update.renamed.items():
                    state[uid] = old_name
            changelog_count -= 1

        return self.model_construct(
            None,
            **kwargs,
            changelog=deepcopy(self.changelog[:changelog_count]),
        )

    def dump_update(
        self,
        fetched: FetchedUser,
        callback: Optional[OutputUpdateCallback] = None,
    ) -> None:
        """Creates a new changelog entry by comparing the dynamically fetched state
        with the latest cached one. It will include users with added/removed/renamed updates
        and will proceed to back it up in a file

        Args:
            fetched (FetchedUser): The dynamically fetched state to use (should not be empty)
            callback (Optional[OutputUpdateCallback]): An optional callback that will be called
                (if provided) for every list providing it with the list name as well as the changes
                as keyword arguments. Can be used for printing the result."""
        entry = CachedChangelogEntry()

        for list_name in LISTS:
            update: CachedUpdate = getattr(entry, list_name)
            update.added = fetched.added_from(self, list_name)  # type: ignore
            update.removed = fetched.removed_from(self, list_name)  # type: ignore
            update.renamed = fetched.renamed_from(self, list_name)  # type: ignore

            if callback is not None:
                callback(
                    list_name,
                    Update(
                        **{
                            change_type: getattr(update, change_type)
                            for change_type in CHANGES
                        }
                    ),
                )

        if fetched.follower_count != len(
            fetched.followers
        ) or fetched.following_count != len(fetched.followings):
            if (
                input(
                    "not all the requested users were fetched, should the result be cached regardless? (Y/n) "
                ).strip()
                != "Y"
            ):
                return

        self.followers = fetched.followers
        self.followings = fetched.followings
        self.changelog.append(entry)

        if not CACHE_FOLDER.is_dir():
            CACHE_FOLDER.mkdir()

        with open(
            CACHE_FOLDER / f"{fetched.id}.json", "w", encoding="utf-8"
        ) as file:
            file.write(self.model_dump_json(indent=2))
        
        UIDMap.get().add_entry(fetched.username, fetched.id)
        logger.info("cached the result")
