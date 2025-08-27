from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from ..models import cached, fetched
from ..utils.bots import Bot
from ..utils.filters import date_filter
from ..utils.parsers import date_parser
from ..utils.renderers import ViewerHistoryRenderer
from ..utils.streams import ColoredOutput


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    args.name = bot.username

    records = cached.StoryHistory.get(args.name)
    renderer = ViewerHistoryRenderer(
        out=ColoredOutput(args.out, "green"),
        username=args.target,
        from_date=args.from_date,
        to_date=args.to_date,
        all=args.all,
        deep=args.deep,
    )

    if args.sync:
        client = bot.login()
        fetched_content = fetched.Stories.fetch(client, args.name, args.chunk_size)
        records.dump_update(fetched_content)

    renderer.render(date_filter(args, reversed(list(records.stories.values()))))


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "target", metavar="target-username", help="The username to lookup"
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.add_argument(
        "--from",
        type=date_parser,
        dest="from_date",
        help="Start date (DD-MM-YYYY) of records to use (defaults to beginning of time)",
    )
    parser.add_argument(
        "--to",
        type=date_parser,
        dest="to_date",
        help="End date (DD-MM-YYYY) of records to use (defaults to current date)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Whether to include stories in the output where the user was not spotted",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="By default only direct name equality is taken "
        "into account for user detection, while this flag "
        "forces the use of its id as well (introducing a "
        "greater overhead)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="By default only cached entries are used, "
        "this makes it so it uses online ones as well",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="In combination with `--sync` controls the size of each chunk of viewers to fetch",
    )
    parser.set_defaults(subfunc=run)
