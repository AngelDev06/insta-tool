import logging
import utils
from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import Optional, Literal
from instagrapi import Client

logger = logging.getLogger("insta-tool-logger")
Cache = Optional[dict[Literal["analyse"], dict[str,
                                                   dict[Literal["followers", "following"], list[str]]]]]


def fetch_followers(client: Client, user_id: int):
    logger.info("fetching followers...")
    return {follower.username for follower in client.user_followers_v1(user_id).values()}


def fetch_following(client: Client, user_id: int):
    logger.info("fetching following...")
    return {following.username for following in client.user_following_v1(user_id).values()}


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
        user_id = client.user_id if args.target == args.name else client.user_id_from_username(args.target)
        followers = fetch_followers(client, user_id)
        logger.info(f"fetched followers (count = {len(followers)})")
        following = fetch_following(client, user_id)
        logger.info(f"fetched following (count = {len(following)})")
        cache["analyse"][args.target] = {"followers": list(followers), "following": list(following)}
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
    parser.add_argument("target", nargs='?', default="", help="The username of the target account")
    parser.add_argument("--reverse", action="store_true",
                        help="reverses the check, i.e. determines which accounts the target doesn't follow back")
    parser.add_argument("--dest", type=Path,
                        help="An optional file to store the result")
    parser.set_defaults(func=run)
