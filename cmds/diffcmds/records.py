from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from ..models import cached, fetched
from ..utils.bots import Bot
from ..utils.constants import CHANGES, LISTS
from ..utils.filters import change_filter, list_filter
from ..utils.parsers import date_parser
from ..utils.renderers import RecordsDiffRenderer
from ..utils.streams import ColoredOutput


def run(args: Namespace) -> None:
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    if not args.target:
        args.target = bot.username

    cached_user = cached.User.get(args.target)
    renderer = RecordsDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        lists=list_filter(args),
        changes=change_filter(args),
        username=args.username,
        detailed=not args.summary,
        from_date=args.date1,
        to_date=args.date2,
    )

    if args.date2 is None:
        client = bot.login()
        record2 = fetched.User.fetch(client, args.target, args.chunk_size)

        if args.date1 is None:
            cached_user.dump_update(record2, renderer.render_block)
            return
        cached_user.dump_update(record2)
    else:
        record2 = cached_user.checkout(args.date2, renderer.lists)

    record1 = (
        cached_user
        if args.date1 is None
        else cached_user.checkout(args.date1, renderer.lists)
    )

    renderer.render(
        record2.updates_from(record1, renderer.lists, renderer.changes)  # type: ignore
    )


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The account whose records will be compared",
    )
    parser.add_argument(
        "date1",
        nargs="?",
        type=date_parser,
        metavar="first-record",
        help="The date (DD-MM-YYYY) of the first record to use (defaults to the most recent one)",
    )
    parser.add_argument(
        "date2",
        nargs="?",
        type=date_parser,
        metavar="second-record",
        help="The date (DD-MM-YYYY) of the second record to use (defaults to fetching from instagram)",
    )
    parser.add_argument(
        "-l",
        "--list",
        choices=LISTS,
        help="An optional to display just the 'followers' or 'following' list "
        "(by default it displays both)",
    )
    parser.add_argument(
        "-c",
        "--change",
        choices=CHANGES,
        help="Display only one change type in the output "
        "(i.e. only added/removed/renamed users)",
    )
    parser.add_argument(
        "--username",
        help="Filter by username (only show updates for a specific user)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display just the number of users added/removed, not the full list",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="If no 'second-record' is specified, this controls "
        "the size of each chunk to request from instagram",
    )
    parser.add_argument(
        "--out",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.set_defaults(subfunc=run)
