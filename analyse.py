import logging
import utils
import functools
from dataclasses import dataclass
from random import randint
from time import sleep
from math import ceil
from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import Optional, Literal, Callable
from instagrapi import Client
from instagrapi.types import UserShort
from instagrapi.exceptions import PleaseWaitFewMinutes

logger = logging.getLogger("insta-tool-logger")
Cache = Optional[dict[Literal["analyse"], dict[str,
                                               dict[Literal["followers", "following"], list[str]]]]]


@dataclass
class ScrapInfo:
    user_name: str
    user_password: str
    user_id: int
    client: Client
    user_count: int
    chunk_size: int
    cursor: str

    @property
    def chunk_amount(self) -> int:
        return ceil(self.user_count / self.chunk_size)

    def report(self):
        logger.info(f"Scraping with: total chunks {self.chunk_amount}, size of each {self.chunk_size}, "
                    f"followers/following count {self.user_count}, user id: {self.user_id}")


def mass_scrap(func: Callable[[ScrapInfo], tuple[list[UserShort], str]]):
    @functools.wraps(func)
    def wrapper(info: ScrapInfo) -> set[str]:
        result: list[UserShort] = []
        cursors: set[str] = set()
        chunk_amount = info.chunk_amount
        info.report()
        cursor_errors: int = 0
        debt: int = 0
        i: int = 0
        while i < chunk_amount:
            logger.info(f"Current chunk number: {i}")
            try:
                user_list, cursor = func(info)
            except PleaseWaitFewMinutes:
                logger.info(
                    "Got rate limited, waiting and re-attempting login...")
                sleep(randint(60, 120))
                info.client.logout()
                info.client.login(info.user_name, info.user_password, relogin=True)
                info.client.dump_settings("session.json")
                info.client.relogin_attempt = 0
                continue
            
            logger.debug(f"Followers/Following got {len(user_list)}, returned cursor: {cursor}")
            
            if cursor in cursors or not cursor:
                logger.debug("invalid cursor received, re-attempting request...")
                continue
            
            cursors.add(cursor)
            info.cursor = cursor
            result += user_list
            i += 1

            if not len(user_list) == info.chunk_size:
                diff = len(user_list) - info.chunk_size
                debt += diff
                logger.debug(f"Debt: {debt}")

            if debt < -info.chunk_size:
                add = -debt // info.chunk_size
                chunk_amount += add
                logger.debug("Chunk amount is not enough to cover user amount")
                logger.debug(f"New chunk amount: {chunk_amount}")
                debt += add * info.chunk_size
            elif debt >= info.chunk_size:
                sub = debt // info.chunk_size
                chunk_amount -= sub
                logger.debug(
                    f"Debt of {debt} reached a chunk size, removing {sub} chunks")
                debt -= sub * info.chunk_size
            elif debt < 0 and chunk_amount == i:
                chunk_amount += 1

            sleep(randint(1, 3))

        logger.info("Scrapping finished")
        return {user.username for user in result}
    return wrapper


@mass_scrap
def fetch_followers(info: ScrapInfo):
    return info.client.user_followers_v1_chunk(info.user_id, info.chunk_size, info.cursor)


@mass_scrap
def fetch_following(info: ScrapInfo):
    return info.client.user_following_v1_chunk(info.user_id, info.chunk_size, info.cursor)


def try_load_from_cache(args: Namespace, cache: Cache):
    if not args.cache:
        return None
    if account := cache["analyse"].get(args.target, None):
        return set(account["followers"]), set(account["following"])
    return None


def run(args: Namespace):
    if not args.target:
        args.target = args.name
    logger.info(f"using target: {args.target}")
    cache: Cache = utils.get_cache()
    cached = try_load_from_cache(args, cache)
    if not cached:
        client = utils.login(args.name, args.password)
        client.delay_range = [1, 3]

        logger.info("fetching user id...")
        user_id = client.user_id if args.target == args.name else int(client.user_id_from_username(
            args.target))

        logger.info("fetching followers/following count...")
        target_user = client.user_info(user_id)

        scrap_info = ScrapInfo(
            user_name=args.name,
            user_password=client.password,
            user_id=user_id,
            client=client,
            user_count=target_user.follower_count,
            chunk_size=50,
            cursor=""
        )

        logger.info("fetching followers...")
        followers = fetch_followers(scrap_info)
        logger.info(f"fetched followers (count = {len(followers)})")

        scrap_info.user_count = target_user.following_count
        logger.info("fetching following...")
        following = fetch_following(scrap_info)
        logger.info(f"fetched following (count = {len(following)})")

        cache["analyse"][args.target] = {"followers": list(
            followers), "following": list(following)}
        utils.update_cache(cache)
    else:
        logger.info("using cached info...")
        followers, following = cached
        logger.info(f"followers count: {len(followers)}")
        logger.info(f"following count: {len(following)}")

    if args.reverse:
        followers, following = following, followers

    with utils.Writer(args.dest) as writer:
        for name in following.difference(followers):
            writer.print(name)


def setup_parser(parser: ArgumentParser):
    parser.add_argument("target", nargs='?', default="",
                        help="The username of the target account")
    parser.add_argument("--reverse", action="store_true",
                        help="reverses the check, i.e. determines which accounts the target doesn't follow back")
    parser.add_argument("--dest", type=Path,
                        help="An optional file to store the result")
    parser.set_defaults(func=run)
