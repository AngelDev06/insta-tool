from argparse import ArgumentParser, FileType, Namespace
from datetime import date, timedelta
from sys import stdout

from . import checkout
from .models import cached, fetched
from .utils.actions import UniqueChoices
from .utils.bots import Bot
from .utils.constants import LISTS
from .utils.renderers import HistoryPointRenderer
from .utils.streams import ColoredOutput


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    if not args.target:
        args.target = bot.username

    cached_user = cached.User.get(args.target)

    if args.sync:
        cached_user.dump_update(
            fetched.User.fetch(bot.login(), args.target, args.chunk_size)
        )

    renderer = HistoryPointRenderer(
        out=ColoredOutput(args.out, "green"),
        history_point=date.today(),
        lists=args.lists,
        target=args.target,
        username=args.username,
        summary=args.summary,
    )
    renderer.render(cached_user)


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
        help="An optional file to output the result",
    )
    parser.add_argument(
        "--lists",
        nargs="+",
        choices=LISTS,
        action=UniqueChoices,
        default=LISTS,
        help="Specify the lists to display",
    )
    parser.add_argument(
        "--username",
        help="Tell whether a specific user is currently a "
        "follower/following of the target account",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display a shorter version (i.e. only "
        "include the counts of followers/followings, not the full list)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Whether to dynamically fetch the current state or use "
        "the latest one in cache",
    )
    parser.set_defaults(func=run)
