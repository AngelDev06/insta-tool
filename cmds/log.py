from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from .models import cached, fetched
from .utils.actions import UniqueChoices
from .utils.bots import Bot
from .utils.constants import CHANGES, LISTS
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
        lists=args.lists,
        changes=args.changes,
        username=args.username,
        detailed=args.detailed,
        target=args.target,
        from_date=args.from_date,
        to_date=args.to_date,
        all=args.all,
    )
    renderer.render(cached_user.changelog)


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
        "--lists",
        nargs="+",
        choices=LISTS,
        action=UniqueChoices,
        default=LISTS,
        help="Filter by list",
    )
    parser.add_argument(
        "--changes",
        nargs="+",
        choices=CHANGES,
        action=UniqueChoices,
        default=CHANGES,
        help="The changes to include in the display (all of them by default)",
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
    parser.set_defaults(func=run)
