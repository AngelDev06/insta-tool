from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from random import randint
from time import sleep
from typing import TYPE_CHECKING, Callable, Optional, TypedDict

from tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client
    from instagrapi.types import UserShort


class UserCache(TypedDict):
    followers: list[str]
    followings: list[str]


@dataclass
class ScrapInfo:
    client: Client
    user_id: str
    user_count: int
    chunk_size: int
    cursor: Optional[str] = ""


def scrap(func: Callable[[ScrapInfo], tuple[list[UserShort], Optional[str]]]):
    @wraps(func)
    def wrapper(info: ScrapInfo) -> set[str]:
        from instagrapi.exceptions import ClientUnauthorizedError

        result: set[str] = set()

        logger.debug(
            "scrapping a total of %d users in chunks of size %d from target with id %s",
            info.user_count,
            info.chunk_size,
            info.user_id,
        )

        while True:
            try:
                user_list, cursor = func(info)
            except ClientUnauthorizedError:
                logger.debug("got rate limited, waiting and re-attempting login...")
                sleep(randint(30, 60))
                client = info.client
                name = client.username
                password = client.password
                client.logout()
                client.login(name, password, relogin=True)
                client.dump_settings("session.json")
                client.relogin_attempt -= 1
                continue

            logger.debug(
                "fetched chunk with total users %d and next cursor being '%s'",
                len(user_list),
                cursor,
            )

            result |= {user.username for user in user_list}
            info.cursor = cursor
            logger.info(f"current user count: {len(result)}")

            if not cursor:
                break

        logger.debug("finished scrapping (no next cursor was returned)")
        return result

    return wrapper


@scrap
def fetch_followers(info: ScrapInfo):
    return info.client.user_followers_gql_chunk(
        info.user_id, info.chunk_size, info.cursor
    )


@scrap
def fetch_followings(info: ScrapInfo):
    return info.client.user_following_gql_chunk(
        info.user_id, info.chunk_size, info.cursor
    )
