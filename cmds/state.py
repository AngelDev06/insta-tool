from argparse import ArgumentParser, FileType, Namespace
from datetime import datetime
from sys import stdout

from . import checkout
from .models import cached, fetched
from .utils.bots import Bot
from .utils.constants import LISTS
from .utils.renderers import HistoryPointRenderer
from .utils.streams import ColoredOutput


def run(args: Namespace):
    if not args.sync:
        checkout.run(
            Namespace(
                date=datetime.now().date(),
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
        history_point=datetime.now().date(),
        lists=LISTS,
        state=state,
        target=args.target,
        username=None,
        summary=args.summary,
    )
    renderer.render()


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
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Specifies the size of each chunk to request when fetching from the api",
    )
    parser.set_defaults(func=run)
