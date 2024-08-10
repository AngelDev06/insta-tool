import sys
from argparse import ArgumentParser, FileType, Namespace

from .login import login
from .utils.scrapping import Scrapper
from .utils.tool_logger import logger
from .utils.user_info import UserInfo


def using_cache(args: Namespace) -> bool:
    if not args.cache:
        return False
    user = UserInfo.from_cache(args.target)
    if user is None:
        return False
    user.dump_difference(args.out, args.reverse)
    return True


def run(args: Namespace):
    if not args.target:
        args.target = args.name
    if using_cache(args):
        return

    client = login(args.name, args.password)
    logger.info(f"fetching profile info of: {args.target}")
    target = client.user_info_by_username_v1(args.target)
    ask_for_cache: bool = False

    for list_name in ("followers", "followings"):
        count: int = (
            target.follower_count
            if list_name == "followers"
            else target.following_count
        )
        scrapper = Scrapper(client, target.pk, count, args.chunk_size)
        logger.info(f"fetching {list_name}, total count {count}")

        if list_name == "followers":
            followers = scrapper.fetch_followers()
        else:
            followings = scrapper.fetch_followings()

        count_received: int = len(locals()[list_name])
        logger.info(f"fetched {list_name}, total count: {count_received}")
        ask_for_cache |= count != count_received

    user = UserInfo(args.target, followers, followings)

    if (
        not ask_for_cache
        or input(
            "not all requested users were fetched, should the result be cached? (Y/n) "
        )
        == "Y"
    ):
        user.to_cache()
        logger.info("cached the result")

    user.dump_difference(args.out, args.reverse)


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
        help="The size of each chunk to request when scrapping",
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
