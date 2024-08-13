import sys
from argparse import ArgumentParser, FileType, Namespace

from .utils.login import get_credentials, login
from .utils.tool_logger import logger
from .utils.user_info import UserInfo


def run(args: Namespace):
    if not args.target:
        if not args.name:
            args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cached = UserInfo.from_cache(args.target)
    if cached is None:
        logger.critical("no user info for the specified target is cached")
        return

    client = login(args.name, args.password)
    fetched = UserInfo.from_api(client, args.target, args.chunk_size, args.retry_max)
    fetched.dump_update(cached, args.out)
    fetched.to_cache()


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "target", nargs="?", default="", help="the account to check for any updates"
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
    parser.add_argument(
        "--retry-max",
        type=int,
        default=3,
        help="Maximum relogin attempts when scrapping",
    )
    parser.set_defaults(func=run)
