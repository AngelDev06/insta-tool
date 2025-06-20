from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from typing import cast
from ..utils.parsers import date_parser
from ..utils.login import get_credentials, login
from ..utils.cache import Cache, UserLists
from ..utils.streams import ColoredOutput
from ..utils.filters import list_filter, change_filter
from ..utils.user_info import UserInfo
from ..utils.renderers import RecordsDiffRenderer


def run(args: Namespace) -> None:
    if not args.target:
        args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cache = Cache(cast(str, args.target))
    renderer = RecordsDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        lists=list_filter(args),
        changes=change_filter(args),
        username=None,
        detailed=not args.summary,
        from_date=args.date1,
        to_date=args.date2,
    )

    if args.date2 is None:
        client = login(args.name, args.password)
        record2 = UserInfo.fetch(client, args.target, args.chunk_size)

        if args.date1 is None:
            cache.dump_update(record2, renderer.render_block)
            return
        cache.dump_update(record2)
    else:
        record2 = cache.checkout(args.date2, renderer.lists)

    record1 = (
        cache.lists
        if args.date1 is None
        else cache.checkout(args.date1, renderer.lists)
    )

    record_table = {"added": (record2, record1), "removed": (record1, record2)}
    renderer.render(
        **{
            change_type: UserLists(
                **{
                    list_name: getattr(record_table[change_type][0], list_name)
                    - getattr(record_table[change_type][1], list_name)
                    for list_name in renderer.lists
                }
            )
            for change_type in renderer.changes
        }
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
        choices=("followers", "followings"),
        help="An optional to display just the 'followers' or 'following' list "
        "(by default it displays both)",
    )
    parser.add_argument(
        "-c",
        "--change",
        choices=("added", "removed"),
        help="Display only one change type in the output "
        "(i.e. only 'added' or 'removed' users, defaults to both)",
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
