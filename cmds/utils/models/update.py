from itertools import chain
from typing import Optional
from dataclasses import dataclass, field


class BasicUpdate:
    added: dict[int, str]
    removed: dict[int, str]
    renamed: dict[int, tuple[str, str]]

    @property
    def added_usernames(self):
        return frozenset(self.added.values())

    @property
    def removed_usernames(self):
        return frozenset(self.removed.values())

    @property
    def renamed_usernames(self):
        return frozenset(
            (
                f"{oldname} -> {newname}"
                for oldname, newname in self.renamed.values()
            )
        )

    def has_username_on_added(self, username: str) -> bool:
        return username in self.added.values()

    def has_username_on_removed(self, username: str) -> bool:
        return username in self.removed.values()

    def has_username_on_renamed(self, username: str) -> bool:
        return username in chain(*self.renamed.values())

    def has_username(self, username: str) -> bool:
        return username in chain(
            self.added.values(), self.removed.values(), *self.renamed.values()
        )

    def is_empty(self, username: Optional[str] = None) -> bool:
        if username is not None:
            return not self.has_username(username)
        return not any((self.added, self.removed, self.renamed))

    def __bool__(self) -> bool:
        return not self.is_empty()


class BasicUserUpdate:
    followers: BasicUpdate
    followings: BasicUpdate

    def has_username(self, username: str) -> bool:
        return self.followers.has_username(
            username
        ) or self.followings.has_username(username)

    def is_empty(self, username: Optional[str] = None) -> bool:
        return self.followers.is_empty(username) and self.followings.is_empty(
            username
        )

    def __bool__(self) -> bool:
        return not self.is_empty()


@dataclass
class Update(BasicUpdate):
    added: dict[int, str] = field(default_factory=dict)
    removed: dict[int, str] = field(default_factory=dict)
    renamed: dict[int, tuple[str, str]] = field(default_factory=dict)


@dataclass
class UserUpdate(BasicUserUpdate):
    followers: Update = field(default_factory=Update)  # type: ignore[override]
    followings: Update = field(default_factory=Update)  # type: ignore[override]
