from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from datetime import datetime
from ..utils.parsers import date_parser
from ..utils.streams import ColoredOutput
from ..utils.login import get_credentials, login
from ..utils.renderers import ListsDiffRenderer
from ..utils.models.cached_user import CachedUser
from ..utils.models.fetched_user import FetchedUser


def run(args: Namespace):
    if not args.target:
        args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cached = CachedUser.get(args.target)  
    renderer = ListsDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        at=args.date,
        reverse=args.reverse,
    )

    if args.date is not None:
        state = cached.checkout(args.date)
    else:
        client = login(args.name, args.password)
        state = FetchedUser.fetch(client, args.target, args.chunk_size)
        cached.dump_update(state)
    
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
