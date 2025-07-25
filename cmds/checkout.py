from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from .utils.parsers import date_parser
from .utils.bots import Bot
from .utils.filters import list_filter
from .utils.streams import ColoredOutput
from .utils.renderers import HistoryPointRenderer
from .utils.models.cached_user import CachedUser
from .utils.constants import LISTS


def run(args: Namespace) -> None:
    if not args.target:
        bot = Bot.get(args.name, args.password, args.tfa_seed)
        args.target = bot.username

    cached = CachedUser.get(args.target)
    if not cached:
        args.out.write(
            "Can't reconstruct a point in history for an untracked user\n"
        )
        return
    lists = list_filter(args)
    renderer = HistoryPointRenderer(
        out=ColoredOutput(args.out, "green"),
        history_point=args.date,
        lists=lists,
        state=cached.checkout(args.date, lists),
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
        choices=LISTS,
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
