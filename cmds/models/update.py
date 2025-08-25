from dataclasses import dataclass, field

from . import mixins


@dataclass
class Update(mixins.Update):
    added: dict[int, str] = field(default_factory=dict)
    removed: dict[int, str] = field(default_factory=dict)
    renamed: dict[int, tuple[str, str]] = field(default_factory=dict)


@dataclass
class UserUpdate(mixins.UserUpdate):
    followers: Update = field(default_factory=Update)  # type: ignore[override]
    followings: Update = field(default_factory=Update)  # type: ignore[override]
