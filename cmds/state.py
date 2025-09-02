from argparse import ArgumentParser, FileType, Namespace
from datetime import date, timedelta
from sys import stdout

from . import checkout
from .models import cached, fetched
from .utils.bots import Bot
from .utils.constants import LISTS
from .utils.renderers import HistoryPointRenderer
from .utils.streams import ColoredOutput
from .utils.actions import UniqueChoices


def run(args: Namespace):
    if not args.sync:
        checkout.run(
            Namespace(
                date=date.today() + timedelta(days=1),
                target=args.target,
                out=args.out,
                list=None,
                username=None,
                summary=args.summary,
            )
        )
        return
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    if not args.target:
        args.target = bot.username
    client = bot.login()
    state = fetched.User.fetch(client, args.target, args.chunk_size)
    cached.User.get(args.target).dump_update(state)
    renderer = HistoryPointRenderer(
        out=ColoredOutput(args.out, "green"),
        history_point=date.today(),
        lists=args.lists,
        target=args.target,
        username=None,
        summary=args.summary,
    )
    renderer.render(state)


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
