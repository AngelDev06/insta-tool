from argparse import ArgumentParser, FileType, Namespace
from datetime import datetime
from sys import stdout
from typing import Union

from ..models import cached, fetched
from ..utils.bots import Bot
from ..utils.parsers import date_parser
from ..utils.renderers import ListsDiffRenderer
from ..utils.streams import ColoredOutput


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    if not args.target:
        args.target = bot.username

    cached_user = cached.User.get(args.target)
    renderer = ListsDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        at=args.date,
        reverse=args.reverse,
    )

    state: Union[cached.User, fetched.User]
    if args.date is not None:
        state = cached_user.checkout(args.date)
    else:
        client = bot.login()
        state = fetched.User.fetch(client, args.target, args.chunk_size)
        cached_user.dump_update(state)

    renderer.render(state.diff(args.reverse))


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="the account whose lists will be compared",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result of the comparison",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="By default followings is compared against followers "
        "to determine who doesn't follow back, so this flag would reverse the check",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--cache",
        nargs="?",
        type=date_parser,
        const=datetime.now().date(),
        dest="date",
        help="Use a cached record instead of fetching lists online with "
        "an optional date (DD-MM-YYYY) that dictates the record to use or "
        "the latest one if not specified",
    )
    group.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="When fetching directly from instagram this dictates "
        "the size of each chunk to request",
    )

    parser.set_defaults(subfunc=run)
