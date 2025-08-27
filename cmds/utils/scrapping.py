from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from random import uniform
from time import sleep, time
from typing import TYPE_CHECKING, Any, Optional, Protocol, cast

from .bots import Config
from .constants import SESSIONS_FOLDER
from .tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client
    from instagrapi.types import UserShort


class ScrapCallback(Protocol):
    def __call__(_self, self: Any) -> tuple[list[UserShort], str]: ...


def scrap(callback: ScrapCallback):
    @wraps(callback)
    def wrapper(self: Any) -> dict[int, str]:
        from instagrapi.exceptions import (
            ChallengeRequired,
            ClientJSONDecodeError,
            ClientUnauthorizedError,
            LoginRequired,
        )

        result: dict[int, str] = {}

        if self.user_count is not None:
            logger.debug(
                "scrapping a total of %d users in chunks of size %d from target with id %s",
                self.user_count,
                self.chunk_size,
                self.target_id,
            )
        else:
            logger.debug(
                "scrapping users in chunks of size %d from target with id %s",
                self.chunk_size,
                self.target_id,
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

            bot = Config.get().bots[self.client.user_id]
            client: Client = self.client
            client.logout()
            client.login(
                bot.username,
                bot.password,
                relogin=True,
                verification_code=bot.tfa_code,
            )
            client.dump_settings(SESSIONS_FOLDER / f"{client.user_id}.json")
            client.relogin_attempt -= 1
            logger.debug("reloged in")
            return True

        while True:
            try:
                user_list, cursor = callback(self)
            except (ClientUnauthorizedError, LoginRequired):
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
            result.update(
                (int(user.pk), cast(str, user.username)) for user in user_list
            )
            logger.info(f"current user count: {len(result)}")

            if not cursor:
                if (
                    self.user_count is not None
                    and len(result) != self.user_count
                    and retry()
                ):
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
    target_id: str
    user_count: Optional[int] = None
    chunk_size: int = 100
    cursor: str = ""

    @scrap
    def fetch_followers(self):
        return self.client.user_followers_gql_chunk(
            self.target_id, self.chunk_size, self.cursor
        )

    @scrap
    def fetch_followings(self):
        return self.client.user_following_gql_chunk(
            self.target_id, self.chunk_size, self.cursor
        )

    @scrap
    def fetch_story_viewers(self):
        return self.client.story_viewers_chunk(
            int(self.target_id), self.chunk_size, self.cursor
        )
