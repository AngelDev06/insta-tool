from sys import stdout
from argparse import ArgumentParser, FileType, Namespace
from typing import TextIO, cast
from termcolor import colored

from .utils.login import get_credentials, login
from .utils.user_info import UserInfo
from .utils.cache import Cache


def output(diff: set[str], out: TextIO) -> None:
    if out is stdout:
        for name in diff:
            out.write(colored(name, "green", attrs=("bold", "underline")))
            out.write("\n")
        return
    for name in diff:
        out.write(f"{name}\n")


def using_cache(args: Namespace) -> bool:
    if not args.cache:
        return False
    user = Cache(cast(str, args.target))
    if not user:
        return False
    output(user.analyse(args.reverse), args.out)
    return True


def run(args: Namespace):
    if not args.target:
        args.name, args.password = get_credentials(
            args.name, args.password
        )
        args.target = args.name

    if using_cache(args):
        return

    client = login(args.name, args.password)
    user = UserInfo.fetch(client, args.target, args.chunk_size)
    output(user.analyse(args.reverse), args.out)
    Cache(cast(str, args.target)).dump_update(user)


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
        default=stdout,
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
        help="Reverses the check, i.e. determines which accounts the target doesn't follow back",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Uses the cache (if available) instead of fetching from instagram",
    )
    parser.set_defaults(func=run)
