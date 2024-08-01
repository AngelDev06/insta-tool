import logging
import utils
import json
from argparse import Namespace, ArgumentParser
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
        client = utils.login(args.name, args.password)
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
