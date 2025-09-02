from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from ..models import cached, fetched
from ..utils.bots import Bot
from ..utils.constants import CHANGES, LISTS
from ..utils.parsers import date_parser
from ..utils.renderers import RecordsDiffRenderer
from ..utils.streams import ColoredOutput
from ..utils.actions import UniqueChoices


def run(args: Namespace) -> None:
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    if not args.target:
        args.target = bot.username

    cached_user = cached.User.get(args.target)
    renderer = RecordsDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        lists=args.lists,
        changes=args.changes,
        username=args.username,
        detailed=not args.summary,
        from_date=args.date1,
        to_date=args.date2,
    )

    if args.date2 is None:
        client = bot.login()
        record2 = fetched.User.fetch(client, args.target, args.chunk_size)

        if args.date1 is None:
            cached_user.dump_update(record2)
            renderer.render(
                cached_user.changelog[-1].pack_updates(
                    args.username, args.lists, args.changes
                )
            )
            return
        cached_user.dump_update(record2)
    else:
        record2 = cached_user.checkout(args.date2, args.lists)

    record1 = (
        cached_user
        if args.date1 is None
        else cached_user.checkout(args.date1, args.lists)
    )

    renderer.render(
        record2.updates_from(record1, args.username, args.lists, args.changes)
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
        metavar="previous-state",
        help="The date (DD-MM-YYYY) of state to use as the previous state. "
        "Any updates that were performed on that date are not included and if "
        "left unspecified the most recent state is used.",
    )
    parser.add_argument(
        "date2",
        nargs="?",
        type=date_parser,
        metavar="after-state",
        help="The date (DD-MM-YYYY) of state to use as the after state. Any "
        "updates that were performed on that date are not included and if left "
        "unspecified the latest state will be fetched from instagram",
    )
    parser.add_argument(
        "-l",
        "--lists",
        nargs="+",
        choices=LISTS,
        action=UniqueChoices,
        default=LISTS,
        help="An optional to display just the 'followers' or 'following' list "
        "(by default it displays both)",
    )
    parser.add_argument(
        "-c",
        "--changes",
        nargs="+",
        choices=CHANGES,
        action=UniqueChoices,
        default=CHANGES,
        help="Display only specific change types in the output",
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
        "--out",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.set_defaults(subfunc=run)
