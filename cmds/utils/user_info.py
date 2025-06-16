from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, Self

from .scrapping import Scrapper
from .tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client


class UserCache(TypedDict):
    followers: list[str]
    followings: list[str]


# dynamic user data obtained directly from the instagram API (unlike UserCache)
@dataclass
class UserInfo:
    username: str
    followers: set[str]
    followings: set[str]
    follower_count: int
    following_count: int

    @classmethod
    def fetch(
        cls, client: Client, username: str, chunk_size: int = 100
    ) -> Self:
        logger.info(f"fetching profile info of: {username}")
        target = client.user_info_by_username_v1(username)

        for list_name in ("followers", "followings"):
            count: int = (
                target.follower_count
                if list_name == "followers"
                else target.following_count
            )
            scrapper = Scrapper(
                client=client,
                user_id=target.pk,
                user_count=count,
                chunk_size=chunk_size,
            )
            logger.info(f"fetching {list_name}, total count: {count}")

            if list_name == "followers":
                followers: set[str] = scrapper.fetch_followers()  # type: ignore
            else:
                followings: set[str] = scrapper.fetch_followings()  # type:ignore

            count_received: int = len(locals()[list_name])
            logger.info(f"fetched {list_name}, total count: {count_received}")

        return cls(
            username,
            followers,  # type: ignore
            followings,  # type: ignore
            target.follower_count,
            target.following_count,
        )

    def analyse(self, reverse: bool) -> set[str]:
        if not reverse:
            return self.followings.difference(self.followers)
        return self.followers.difference(self.followings)
