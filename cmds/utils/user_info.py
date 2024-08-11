from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TextIO, TypedDict

from termcolor import colored

from .scrapping import Scrapper
from .tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client


class UserCache(TypedDict):
    followers: list[str]
    followings: list[str]


@dataclass
class UserInfo:
    username: str
    followers: set[str]
    followings: set[str]
    follower_count: int
    following_count: int

    @classmethod
    def from_cache(cls, username: str) -> "Optional[UserInfo]":
        path = Path("user info") / f"{username}.json"
        if not path.is_file():
            return None

        with open(path, encoding="utf-8") as file:
            cache: UserCache = json.load(file)
        return cls(
            username,
            set(cache["followers"]),
            set(cache["followings"]),
            len(cache["followers"]),
            len(cache["followings"]),
        )

    @classmethod
    def from_api(
        cls, client: Client, username: str, chunk_size: int = 100
    ) -> "UserInfo":
        logger.info(f"fetching profile info of: {username}")
        target = client.user_info_by_username_v1(username)

        for list_name in ("followers", "followings"):
            count: int = (
                target.follower_count
                if list_name == "followers"
                else target.following_count
            )
            scrapper = Scrapper(client, target.pk, count, chunk_size)
            logger.info(f"fetching {list_name}, total count {count}")

            if list_name == "followers":
                followers = scrapper.fetch_followers()
            else:
                followings = scrapper.fetch_followings()

            count_received: int = len(locals()[list_name])
            logger.info(f"fetched {list_name}, total count: {count_received}")

        return cls(
            username,
            followers,
            followings,
            target.follower_count,
            target.following_count,
        )

    def to_cache(self):
        if self.follower_count != len(self.followers) or self.following_count != len(
            self.followings
        ):
            if (
                input(
                    "not all the requested users were fetched, should the result be cached regardless? (Y/n) "
                )
                != "Y"
            ):
                return

        data = {"followers": list(self.followers), "followings": list(self.followings)}
        root = Path("user info")
        if not root.is_dir():
            root.mkdir()

        with open(root / f"{self.username}.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        logger.info("cached the result")

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

    def dump_update(self, other: "UserInfo", out: TextIO):
        for list_name in ("followers", "followings"):
            current_list: set[str] = getattr(self, list_name)
            other_list: set[str] = getattr(other, list_name)
            new_users = current_list.difference(other_list)
            removed_users = other_list.difference(current_list)

            if not new_users and not removed_users:
                out.write(f"{list_name} list: no update\n")
                continue

            out.write(f"{list_name} list:\n")

            if new_users:
                out.write(f"\tnew {list_name}:")
                for user in new_users:
                    if out is sys.stdout:
                        out.write("\n\t\t")
                        out.write(
                            colored(f"+ {user}", "green", attrs=("bold", "underline"))
                        )
                    else:
                        out.write(f"\n\t\t+ {user}")

                out.write("\n")

            if removed_users:
                out.write(f"\tremoved {list_name}:")
                for user in removed_users:
                    if out is sys.stdout:
                        out.write("\n\t\t")
                        out.write(
                            colored(f"- {user}", "red", attrs=("bold", "underline"))
                        )
                    else:
                        out.write(f"\n\t\t- {user}")

                out.write("\n")
