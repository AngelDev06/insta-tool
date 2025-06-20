from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from typing import cast
from .utils.parsers import date_parser
from .utils.login import get_credentials
from .utils.cache import Cache
from .utils.filters import list_filter
from .utils.streams import ColoredOutput
from .utils.renderers import HistoryPointRenderer


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
    lists = list_filter(args)
    renderer = HistoryPointRenderer(
        out=ColoredOutput(args.out, "green"),
        history_point=args.date,
        lists=lists,
        user_lists=cache.checkout(args.date, lists),
        target=args.target,
        username=args.username,
        summary=args.summary,
    )
    renderer.render()


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
