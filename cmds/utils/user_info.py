import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TextIO, TypedDict

from termcolor import colored


class UserCache(TypedDict):
    followers: list[str]
    followings: list[str]


@dataclass
class UserInfo:
    username: str
    followers: set[str]
    followings: set[str]

    @classmethod
    def from_cache(cls, username: str) -> "Optional[UserInfo]":
        path = Path("user info") / f"{username}.json"
        if not path.is_file():
            return None

        with open(path, encoding="utf-8") as file:
            cache: UserCache = json.load(file)
        return cls(username, set(cache["followers"]), set(cache["followings"]))

    def to_cache(self):
        data = {"followers": list(self.followers), "followings": list(self.followings)}
        root = Path("user info")
        if not root.is_dir():
            root.mkdir()

        with open(root / f"{self.username}.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def dump_difference(self, out: TextIO, reverse: bool = False):
        diff = (
            self.followings.difference(self.followers)
            if not reverse
            else self.followers.difference(self.followings)
        )

        if out is sys.stdout:

            def with_color(text: str) -> str:
                return colored(text, "green", attrs=("bold", "underline"))

        else:

            def with_color(text: str) -> str:
                return text

        for name in diff:
            out.write(with_color(name))
            out.write("\n")
