from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from random import uniform
from time import sleep, time
from typing import TYPE_CHECKING, Callable, cast

from .tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client
    from instagrapi.types import UserShort


def scrap(func: Callable[[Scrapper], tuple[list[UserShort], str]]):
    @wraps(func)
    def wrapper(self: "Scrapper") -> set[str]:
        from instagrapi.exceptions import (
            ChallengeRequired,
            ClientJSONDecodeError,
            ClientUnauthorizedError,
        )

        result: set[str] = set()

        logger.debug(
            "scrapping a total of %d users in chunks of size %d from target with id %s",
            self.user_count,
            self.chunk_size,
            self.user_id,
        )

        def retry() -> bool:
            start = time()
            if (
                input(
                    "loop was terminated by instagram before fetching all users, should it continue trying? (Y/n) "
                ).strip()
                != "Y"
            ):
                return False

            diff = time() - start
            duration = uniform(5, 10)
            if duration > diff:
                duration -= diff
                logger.debug("sleeping for %f seconds", duration)
                sleep(duration)

            client = self.client
            name = client.username
            password = client.password
            client.logout()
            client.login(name, password, relogin=True)
            client.dump_settings("session.json")  # type: ignore
            client.relogin_attempt -= 1
            logger.debug("reloged in")
            return True

        while True:
            try:
                user_list, cursor = func(self)
            except ClientUnauthorizedError:
                if not retry():
                    break
                continue
            except (ClientJSONDecodeError, ChallengeRequired):
                if (
                    input(
                        "json decode failure possibly due to a challenge, should it continue? (Y/n) "
                    ).strip()
                    == "Y"
                ):
                    continue
                break

            logger.debug(
                "fetched chunk with total users %d and next cursor being '%s'",
                len(user_list),
                cursor,
            )

            result |= {cast(str, user.username) for user in user_list}
            logger.info(f"current user count: {len(result)}")

            if not cursor:
                if len(result) != self.user_count and retry():
                    continue
                break

            self.cursor = cursor
            sleep(uniform(2, 4))

        logger.debug("finished scrapping (no next cursor was returned)")
        return result

    return wrapper


@dataclass
class Scrapper:
    client: Client
    user_id: str
    user_count: int
    chunk_size: int
    cursor: str = ""

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
