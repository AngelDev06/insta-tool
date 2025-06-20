from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from typing import cast
from .utils.login import get_credentials, login
from .utils.cache import Cache
from .utils.user_info import UserInfo
from .utils.filters import date_filter, list_filter, change_filter
from .utils.parsers import date_parser
from .utils.renderers import ChangelogRenderer
from .utils.streams import ColoredOutput


def run(args: Namespace) -> None:
    if not args.target:
        args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cache = Cache(cast(str, args.target))

    if args.sync:
        client = login(args.name, args.password)
        fetched = UserInfo.fetch(client, args.target, args.chunk_size)
        cache.dump_update(fetched)
    elif not cache:
        args.out.write(f"No logs to display for '{args.target}'\n")
        return

    renderer = ChangelogRenderer(
        out=ColoredOutput(args.out, "green"),
        lists=list_filter(args),
        changes=change_filter(args),
        username=args.username,
        detailed=args.detailed,
        target=args.target,
        changelog=date_filter(args, reversed(cache.changelog)),
        all=args.all
    )
    renderer.render()


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The username of the account to log info for",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the logging info",
    )
    parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Display detailed information (i.e. the entire list of followers/followings added/removed)",
    )
    parser.add_argument(
        "--from-date", type=date_parser, help="Start date (DD-MM-YYYY)"
    )
    parser.add_argument(
        "--to-date", type=date_parser, help="End date (DD-MM-YYYY)"
    )
    parser.add_argument(
        "--list",
        choices=("followers", "followings"),
        help="Filter by list (only display followers or followings)",
    )
    parser.add_argument(
        "--change",
        choices=("added", "removed"),
        help="Only display 'added' or 'removed' users (applies to each list)",
    )
    parser.add_argument(
        "--username",
        help="Filter by username (only show updates for a specific user)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Include empty logs in the display "
            "(note that some filters make logs be considered empty "
            "such as with '--username' when the user isn't there)"
        ),
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Whether it should (in addition) create a new log by fetching current info",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Only matters if --sync is specified and controls the size of each chunk to fetch while scrapping",
    )
    parser.set_defaults(func=run)
