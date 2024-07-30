import logging
import utils
import functools
import json
from itertools import count
from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import Optional, Literal, Callable
from ensta import Web

logger = logging.getLogger("insta-tool-logger")


def mass_scrap(func: Callable[[Web, str], set[str]]):
    @functools.wraps(func)
    def wrapper(client: Web, target_id: str, user_count: int) -> set[str]:
        result: set[str] = set()
        for i in count(1):
            logger.debug("attempt count: %d", i)
            users = func(client, target_id)
            logger.debug("user count returned: %d", len(users))
            result |= users

            if len(result) == user_count:
                break
            logger.debug(
                "only %d/%d users were retrieved, re-attempting fetch...",
                len(result),
                user_count,
            )
        return result

    return wrapper


@mass_scrap
def fetch_followers(client: Web, target_id: str) -> set[str]:
    return {follower.username for follower in client.followers(target_id)}


@mass_scrap
def fetch_followings(client: Web, target_id: str) -> set[str]:
    return {following.username for following in client.followings(target_id)}


def from_cache(args: Namespace) -> Optional[tuple[set[str], set[str]]]:
    if not args.cache:
        return None
    cache_path = Path("user info") / f"{args.target}.json"
    if not cache_path.is_file():
        return None
    with open(cache_path, encoding="utf-8") as file:
        cache: dict[Literal["followers", "followings"], list[str]] = json.load(
            file
        )
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
        client = utils.login(args.name, args.password)
        logger.info(f"fetching profile info of: {args.target}")
        target = client.profile(args.target)

        logger.info(
            f"fetching followers, total count: {target.follower_count}"
        )
        followers = fetch_followers(
            client, target.user_id, target.follower_count
        )
        logger.info(f"fetched followers, total count: {len(followers)}")

        logger.info(
            f"fetching followings, total count: {target.following_count}"
        )
        followings = fetch_followings(
            client, target.user_id, target.following_count
        )
        logger.info(f"fetched followings, total count: {len(followings)}")

        to_cache(args.target, followers, followings)
        logger.info("cached the result")

    if args.reverse:
        followers, followings = followings, followers

    with utils.Writer(args.dest) as writer:
        for name in followings.difference(followers):
            writer.print(name)


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The username of the target account",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="reverses the check, i.e. determines which accounts the target doesn't follow back",
    )
    parser.add_argument(
        "--dest", type=Path, help="An optional file to store the result"
    )
    parser.set_defaults(func=run)
