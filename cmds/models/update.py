from dataclasses import dataclass, field
from typing import Optional, Protocol, TypeAlias, Union

from ..utils.constants import ChangesType


class SupportsStr(Protocol):
    def __str__(self) -> str: ...


StrLike: TypeAlias = Union[str, SupportsStr]


@dataclass
class RenamedUser:
    old: StrLike
    new: StrLike

    def __str__(self) -> str:
        return f"{self.old} -> {self.new}"


@dataclass
class Update:
    added: dict[int, StrLike] = field(default_factory=dict)
    removed: dict[int, StrLike] = field(default_factory=dict)
    renamed: dict[int, RenamedUser] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return any((self.added, self.removed, self.renamed))


@dataclass
class SingleUpdate:
    change: Optional[ChangesType] = None
    user_id: Optional[int] = None
    username: Optional[StrLike] = None

    def __bool__(self) -> bool:
        return all((self.change, self.user_id, self.username))


@dataclass
class UserUpdate:
    followers: Optional[Union[Update, SingleUpdate]] = None
    followings: Optional[Union[Update, SingleUpdate]] = None

    def __bool__(self) -> bool:
        return bool(self.followers or self.followings)
