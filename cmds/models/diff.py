from dataclasses import dataclass, field
from typing import Optional, Protocol, TypeAlias, Union

from ..utils.constants import DiffsType


class SupportsStr(Protocol):
    def __str__(self) -> str: ...


StrLike: TypeAlias = Union[str, SupportsStr]


@dataclass
class Diff:
    user1: dict[int, StrLike] = field(default_factory=dict)
    user2: dict[int, StrLike] = field(default_factory=dict)
    mutuals: dict[int, StrLike] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return any((self.user1, self.user2, self.mutuals))


@dataclass
class SingleDiff:
    change: Optional[DiffsType] = None
    user_id: Optional[int] = None
    username: Optional[StrLike] = None

    def __bool__(self) -> bool:
        return all((self.change, self.user_id, self.username))


@dataclass
class UserDiff:
    followers: Union[Diff, SingleDiff]
    followings: Union[Diff, SingleDiff]

    def __bool__(self) -> bool:
        return bool(self.followers or self.followings)
