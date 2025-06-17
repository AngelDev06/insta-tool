import sys
from argparse import ArgumentParser, FileType, Namespace
from typing import cast

from .utils.login import get_credentials, login
from .utils.tool_logger import logger
from .utils.user_info import UserInfo
from .utils.cache import Cache


def run(args: Namespace):
    if not args.target:
        args.name, args.password = get_credentials(
            args.name, args.password
        )
        args.target = args.name

    cached = Cache(cast(str, args.target))
    if not cached:
        logger.info(
            "no user info is currently cached, "
            "all followers/followings fetched will be treated as new additions"
        )

    client = login(args.name, args.password)
    fetched = UserInfo.fetch(client, args.target, args.chunk_size)
    cached.dump_update(fetched, args.out)


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="the account to check for any updates",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=sys.stdout,
        help="an optional file to output the result",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="The size of each chunk to request when scrapping",
    )
    parser.set_defaults(func=run)
