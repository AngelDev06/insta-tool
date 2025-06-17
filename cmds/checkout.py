from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from typing import cast, TextIO, Iterable
from datetime import date
from termcolor import colored
from .utils.parsers import date_parser
from .utils.login import get_credentials
from .utils.cache import Cache, UserCache
from .utils.filters import list_filter


def output(args: Namespace, cache: UserCache) -> None:
    out: TextIO = args.out
    history_point: date = args.date
    lists = list_filter(args)
    list_table = {
        "followers": set(cache.followers),
        "followings": set(cache.followings),
    }

    def style(
        text: str,
        color: str = "green",
        attrs: Iterable[str] = ("bold", "underline"),
    ) -> str:
        return colored(text, color, attrs=attrs) if out is stdout else text

    for log in reversed(cache.changelog):
        log_date = date.fromtimestamp(log["timestamp"])
        if log_date <= history_point:
            break

        for list_name in lists:
            list_table[list_name] -= set(log[list_name]["added"])
            list_table[list_name] |= set(log[list_name]["removed"])

    history_point_text = history_point.strftime("%d/%m/%Y")
    out.write(f"History for {args.target} at {history_point_text}\n")

    text_table = {"followers": "", "followings": ""}

    for list_name in lists:
        if args.username is not None:
            if args.username in list_table[list_name]:
                text_table[list_name] = f"a {list_name[:-1]}"
            continue
        if args.summary:
            out.write(
                f"{list_name.capitalize()}: {len(list_table[list_name])}\n"
            )
            continue

        out.write(
            f"{list_name.capitalize()} ({len(list_table[list_name])}):\n"
        )

        for username in list_table[list_name]:
            out.write("  ")
            out.write(style(username))
            out.write("\n")

    if args.username is not None:
        separator = ""
        if not text_table["followers"] and not text_table["followings"]:
            out.write(f"{args.username} was neither a follower nor a following")
            return
        if text_table["followers"] and text_table["followings"]:
            separator = " and "
        out.write(
            f"{args.username} was "
            f"{text_table['followers']}{separator}{text_table['followings']} "
            f"of {args.target}\n"
        )


def run(args: Namespace) -> None:
    if not args.target:
        args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cache = Cache(cast(str, args.target))
    if not cache:
        args.out.write(
            "Can't reconstruct a point in history for an untracked user\n"
        )
        return
    output(args, cache)


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "date",
        type=date_parser,
        help="The date based on which history will be reconstructed (DD-MM-YYYY)",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The username of the account to reconstruct history for",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.add_argument(
        "--list",
        choices=("followers", "followings"),
        help="Display only either 'followers' or 'followings' list",
    )
    parser.add_argument(
        "--username",
        help="Tell whether a user was a follower/following at the specified point in history",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display a shorter version (i.e. just the follower/following count, not the entire list)",
    )
    parser.set_defaults(func=run)
