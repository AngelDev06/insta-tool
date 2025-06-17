from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from typing import cast, TextIO, Iterable
from datetime import datetime
from termcolor import colored
from .utils.login import get_credentials, login
from .utils.cache import Cache, UserCache
from .utils.user_info import UserInfo


def output(args: Namespace, cache: UserCache) -> None:
    out: TextIO = args.out
    out.write(f"Logs for {args.target}\n\n")

    def style(
        text: str, color: str, attrs: Iterable[str] = ("bold", "underline")
    ) -> str:
        return colored(text, color, attrs=attrs) if out is stdout else text

    for log in reversed(cache.changelog):
        date = datetime.fromtimestamp(log["timestamp"]).strftime(
            "%d/%m/%Y %I:%M:%S%p"
        )
        out.write(f"Changelog - {date}\n")

        for list_name in ("followers", "followings"):
            out.write(f"{list_name.capitalize()}:\n")

            for change_type, sign, color in (
                ("added", "+", "green"),
                ("removed", "-", "red"),
            ):
                out.write("  ")
                out.write(
                    style(
                        f"{sign}{len(log[list_name][change_type])} {change_type}",
                        color,
                        attrs=("bold",),
                    )
                )
                out.write("\n")

                if not args.detailed:
                    continue

                for username in log[list_name][change_type]:
                    out.write("    ")
                    out.write(style(f"{sign} {username}", color))
                    out.write("\n")

        out.write("\n")


def run(args: Namespace) -> None:
    if not args.target:
        args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cache = Cache(cast(str, args.target))

    if args.sync:
        client = login(args.name, args.password)
        fetched = UserInfo.fetch(client, args.target, args.chunk_size)
        cache.dump_update(fetched)
    elif not cache:
        args.out.write(f"No logs to display for '{args.target}'\n")
        return
    
    output(args, cache)


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The username of the account to log info for",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the logging info",
    )
    parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Display detailed information (i.e. the entire list of followers/followings added/removed)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Whether it should (in addition) create a new log by fetching current info",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Only matters if --sync is specified and controls the size of each chunk to fetch while scrapping",
    )
    parser.set_defaults(func=run)
