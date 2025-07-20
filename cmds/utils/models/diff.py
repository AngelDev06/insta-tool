from dataclasses import dataclass, field
from itertools import chain
from typing import Optional


@dataclass
class Diff:
    user1: dict[int, str] = field(default_factory=dict)
    user2: dict[int, str] = field(default_factory=dict)
    mutuals: dict[int, str] = field(default_factory=dict)

    @property
    def user1_usernames(self):
        return frozenset(self.user1.values())

    @property
    def user2_usernames(self):
        return frozenset(self.user2.values())

    @property
    def mutuals_usernames(self):
        return frozenset(self.mutuals.values())

    def has_username_on_user1(self, username: str) -> bool:
        return username in self.user1.values()

    def has_username_on_user2(self, username: str) -> bool:
        return username in self.user2.values()

    def has_username_on_mutuals(self, username: str) -> bool:
        return username in self.mutuals.values()

    def has_username(self, username: str) -> bool:
        return username in chain(
            self.user1.values(), self.user2.values(), self.mutuals.values()
        )

    def is_empty(self, username: Optional[str] = None) -> bool:
        if username is not None:
            return not self.has_username(username)
        return not any((self.user1, self.user2, self.mutuals))

    def __bool__(self) -> bool:
        return not self.is_empty()


@dataclass
class UserDiff:
    followers: Diff
    followings: Diff

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
