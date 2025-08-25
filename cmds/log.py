from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from .models import cached, fetched
from .utils.bots import Bot
from .utils.constants import CHANGES, LISTS
from .utils.filters import change_filter, date_filter, list_filter
from .utils.parsers import date_parser
from .utils.renderers import ChangelogRenderer
from .utils.streams import ColoredOutput


def run(args: Namespace) -> None:
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    if not args.target:
        args.target = bot.username

    cached_user = cached.User.get(args.target)

    if args.sync:
        client = bot.login()
        fetched_user = fetched.User.fetch(client, args.target, args.chunk_size)
        cached_user.dump_update(fetched_user)
    elif not cached_user:
        args.out.write(f"No logs to display for '{args.target}'\n")
        return

    renderer = ChangelogRenderer(
        out=ColoredOutput(args.out, "green"),
        lists=list_filter(args),
        changes=change_filter(args),
        username=args.username,
        detailed=args.detailed,
        target=args.target,
        changelog=date_filter(args, reversed(cached_user.changelog)),
        all=args.all,
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
    parser.add_argument("--from-date", type=date_parser, help="Start date (DD-MM-YYYY)")
    parser.add_argument("--to-date", type=date_parser, help="End date (DD-MM-YYYY)")
    parser.add_argument(
        "--list",
        choices=LISTS,
        help="Filter by list (only display followers or followings)",
    )
    parser.add_argument(
        "--change",
        choices=CHANGES,
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
