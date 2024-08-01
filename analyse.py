import logging
import json
import sys
from login import login
from termcolor import colored
from argparse import Namespace, ArgumentParser, FileType
from pathlib import Path
from typing import Optional, Literal
from ensta import Web

logger = logging.getLogger("insta-tool-logger")


def fetch_followers(client: Web, target_id: str, count: int) -> set[str]:
    logger.info(f"fetching followers, total count: {count}")
    result = {follower.username for follower in client.followers(target_id)}
    logger.info(f"fetched followers, total count: {len(result)}")
    return result


def fetch_followings(client: Web, target_id: str, count: int) -> set[str]:
    logger.info(f"fetching followings, total count: {count}")
    result = {following.username for following in client.followings(target_id)}
    logger.info(f"fetched followings, total count: {len(result)}")
    return result


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
        client = login(args.name, args.password)
        logger.info(f"fetching profile info of: {args.target}")
        target = client.profile(args.target)

        followers = fetch_followers(
            client, target.user_id, target.follower_count
        )
        followings = fetch_followings(
            client, target.user_id, target.following_count
        )

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
        args.out.write('\n')


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
        help="An optional file to output the result, defaults to stdout"
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="reverses the check, i.e. determines which accounts the target doesn't follow back",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Uses the cache (if available) instead of fetching from instagram"
    )
    parser.set_defaults(func=run)
