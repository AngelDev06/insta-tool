from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from random import randint
from time import sleep
from typing import TYPE_CHECKING, Callable, Optional

from .tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client
    from instagrapi.types import UserShort


def scrap(func: Callable[[Scrapper], tuple[list[UserShort], str]]):
    @wraps(func)
    def wrapper(self: "Scrapper") -> set[str]:
        from instagrapi.exceptions import ClientUnauthorizedError

        result: set[str] = set()

        logger.debug(
            "scrapping a total of %d users in chunks of size %d from target with id %s",
            self.user_count,
            self.chunk_size,
            self.user_id,
        )

        while True:
            try:
                user_list, cursor = func(self)
            except ClientUnauthorizedError:
                logger.debug("got rate limited, waiting and re-attempting login...")
                sleep(randint(30, 60))
                client = self.client
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
            self.cursor = cursor
            logger.info(f"current user count: {len(result)}")

            if not cursor:
                break

            sleep(randint(1, 3))

        logger.debug("finished scrapping (no next cursor was returned)")
        return result

    return wrapper


@dataclass
class Scrapper:
    client: Client
    user_id: str
    user_count: int
    chunk_size: int
    cursor: Optional[str] = ""

    @scrap
    def fetch_followers(self):
        return self.client.user_followers_gql_chunk(
            self.user_id, self.chunk_size, self.cursor
        )

    @scrap
    def fetch_followings(self):
        return self.client.user_following_gql_chunk(
            self.user_id, self.chunk_size, self.cursor
        )
