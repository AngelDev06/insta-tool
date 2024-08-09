import json
import logging
import sys
from argparse import ArgumentParser, FileType, Namespace
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from random import randint
from time import sleep
from typing import Callable, Literal, Optional, TypedDict

from instagrapi import Client
from instagrapi.exceptions import PleaseWaitFewMinutes
from instagrapi.types import UserShort
from termcolor import colored

from login import login

logger = logging.getLogger("insta-tool-logger")


class UserCache(TypedDict):
    followers: list[str]
    followings: list[str]


@dataclass
class ScrapInfo:
    client: Client
    user_id: str
    chunk_size: int
    cursor: Optional[str] = ""


def scrap(func: Callable[[ScrapInfo], tuple[list[UserShort], Optional[str]]]):
    @wraps(func)
    def wrapper(info: ScrapInfo) -> set[str]:
        result: set[str] = set()

        while info.cursor is not None:
            try:
                user_list, cursor = func(info)
            except PleaseWaitFewMinutes:
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
                "fetched chunk with total users %d and next cursor being %s",
                len(user_list),
                cursor,
            )
            result |= set(user_list)
            info.cursor = cursor
            logger.info(f"current user count: {len(result)}")
            sleep(randint(1, 3))

        logger.debug("finished scrapping (no next cursor was returned)")
        return result

    return wrapper


@scrap
def fetch_followers(info: ScrapInfo):
    return info.client.user_followers_v1_chunk(
        info.user_id, info.chunk_size, info.cursor
    )


@scrap
def fetch_followings(info: ScrapInfo):
    return info.client.user_following_v1_chunk(
        info.user_id, info.chunk_size, info.cursor
    )


def from_cache(args: Namespace) -> Optional[tuple[set[str], set[str]]]:
    if not args.cache:
        return None
    cache_path = Path("user info") / f"{args.target}.json"
    if not cache_path.is_file():
        return None
    with open(cache_path, encoding="utf-8") as file:
        cache: UserCache = json.load(file)
    return set(cache["followers"]), set(cache["followings"])


def to_cache(target: str, followers: set[str], followings: set[str]):
    cache_dir = Path("user info")
    if not cache_dir.is_dir():
        cache_dir.mkdir()
    with open(cache_dir / f"{target}.json", "w", encoding="utf-8") as file:
        data = {"followers": list(followers), "followings": list(followings)}
        json.dump(data, file, indent=2)


def run(args: Namespace):
    if not args.target:
        args.target = args.name

    if cache := from_cache(args):
        logger.info(f"using cached info for: {args.target}")
        followers, followings = cache
    else:
        client = login(args.name, args.password)
        logger.info(f"fetching profile info of: {args.target}")
        target = client.user_info_by_username(args.target)

        for list_name in ("followers", "followings"):
            count: int = (
                target.follower_count
                if list_name == "followers"
                else target.following_count
            )
            info = ScrapInfo(client=client, user_id=target.pk, chunk_size=args.chunk_size)
            logger.info(f"fetching {list_name}, total count: {count}")

            if list_name == "followers":
                followers = fetch_followers(info)
            else:
                followings = fetch_followings(info)

            logger.info(f"fetched {list_name}, total count: {len(locals()[list_name])}")

        to_cache(args.target, followers, followings)
        logger.info("cached the result")

    if args.reverse:
        followers, followings = followings, followers

    if args.out is sys.stdout:

        def with_color(text: str) -> str:
            return colored(text, "green", attrs=("bold", "underline"))

    else:

        def with_color(text: str) -> str:
            return text

    for name in followings.difference(followers):
        args.out.write(with_color(name))
        args.out.write("\n")


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The username of the target account",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=sys.stdout,
        help="An optional file to output the result, defaults to stdout",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="The size of each chunk to request when scrapping"
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="reverses the check, i.e. determines which accounts the target doesn't follow back",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Uses the cache (if available) instead of fetching from instagram",
    )
    parser.set_defaults(func=run)
