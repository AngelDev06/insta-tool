import sys
from argparse import ArgumentParser, FileType, Namespace

from .utils.login import get_credentials, login
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
        if not args.name:
            args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    if using_cache(args):
        return

    client = login(args.name, args.password)
    user = UserInfo.from_api(client, args.target, args.chunk_size)
    user.to_cache()
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
