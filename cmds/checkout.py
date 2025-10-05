from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from .models import cached
from .utils.actions import UniqueChoices
from .utils.bots import Bot
from .utils.constants import LISTS
from .utils.parsers import date_parser
from .utils.renderers import HistoryPointRenderer
from .utils.streams import ColoredOutput


def run(args: Namespace) -> None:
    if not args.target:
        bot = Bot.get(args.name, args.password, args.tfa_seed)
        args.target = bot.username

    renderer = HistoryPointRenderer(
        out=ColoredOutput(args.out, "green"),
        history_point=args.date,
        lists=args.lists,
        target=args.target,
        username=args.username,
        summary=args.summary,
    )

    cached_user = cached.User.get(args.target)
    if not cached_user:
        args.out.write(
            "Can't reconstruct a point in history for an untracked user\n"
        )
        return
    renderer.render(cached_user.checkout(args.date, renderer.lists))


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "date",
        type=date_parser,
        help="The date based on which history will be reconstructed (DD-MM-YYYY). "
        "Any updates performed on that date will have no effect in the state displayed",
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
        "--lists",
        nargs="+",
        choices=LISTS,
        action=UniqueChoices,
        default=LISTS,
        help="Specify the lists to display (defaults to both followers and followings)",
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
