from __future__ import annotations
from typing import TYPE_CHECKING, Self
from dataclasses import dataclass
from .user import BasicUser
from ..tool_logger import logger
from ..scrapping import Scrapper
from ..constants import LISTS, ListsType

if TYPE_CHECKING:
    from instagrapi import Client


@dataclass
class FetchedUser(BasicUser):
    username: str
    id: int
    followers: dict[int, str]
    followings: dict[int, str]
    follower_count: int
    following_count: int

    @classmethod
    def fetch(
        cls, client: Client, username: str, chunk_size: int = 100
    ) -> Self:
        logger.info(f"fetching profile info of: {username}")
        target = client.user_info_by_username_v1(username)
        list_table: dict[ListsType, dict[int, str]] = {}

        for list_name in LISTS:
            count: int = getattr(target, f"{list_name[:-1]}_count")
            scrapper = Scrapper(
                client=client,
                user_id=target.pk,
                user_count=count,
                chunk_size=chunk_size,
            )
            logger.info(f"fetching {list_name}, total count: {count}")
            user_list: dict[int, str] = getattr(
                scrapper, f"fetch_{list_name}"
            )()
            list_table[list_name] = user_list
            logger.info(f"fetched {list_name}, total count: {len(user_list)}")

        return cls(
            username=username,
            id=int(target.pk),
            **list_table,
            follower_count=target.follower_count,
            following_count=target.following_count,
        )
