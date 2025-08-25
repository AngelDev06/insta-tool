from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from ...utils.constants import LISTS, ListsType
from ...utils.scrapping import Scrapper
from ...utils.tool_logger import logger
from .. import mixins

if TYPE_CHECKING:
    from instagrapi import Client


@dataclass
class User(mixins.User):
    username: str
    id: int = 0
    followers: dict[int, str] = field(default_factory=dict)
    followings: dict[int, str] = field(default_factory=dict)
    follower_count: int = 0
    following_count: int = 0

    @classmethod
    def fetch(
        cls,
        client: Client,
        username: str,
        chunk_size: int = 100,
    ) -> Self:
        logger.info(f"fetching profile info of: {username}")
        target = client.user_info_by_username_v1(username)
        container: dict[ListsType, dict[int, str]] = {}

        for list_name in LISTS:
            count: int = getattr(target, f"{list_name[:-1]}_count")
            scrapper = Scrapper(
                client=client,
                target_id=target.pk,
                user_count=count,
                chunk_size=chunk_size,
            )
            logger.info(f"fetching {list_name}, total count: {count}")
            user_list: dict[int, str] = getattr(scrapper, f"fetch_{list_name}")()
            container[list_name] = user_list

            logger.info(f"fetched {list_name}, total count: {len(user_list)}")

        return cls(
            username=target.username,
            id=int(target.pk),
            follower_count=target.follower_count,
            following_count=target.following_count,
            **container,
        )
