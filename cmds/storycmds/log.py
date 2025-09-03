from argparse import ArgumentParser, Namespace, FileType
from sys import stdout
from ..utils.actions import UniqueChoices
from ..utils.parsers import id_or_date
from ..utils.constants import CHANGES
from ..utils.bots import Bot
from ..utils.renderers import ViewersChangelogRenderer
from ..utils.streams import ColoredOutput
from ..models import fetched, cached


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    args.name = bot.username

    records = cached.StoryHistory.get(args.name)

    if args.sync:
        records.dump_update(
            fetched.Stories.fetch(bot.login(), args.name, args.chunk_size)
        )

    renderer = ViewersChangelogRenderer(
        out=ColoredOutput(args.out, "green"),
        changes=args.changes,
        username=args.username,
        detailed=args.detailed,
        target=args.name,
        from_record=args.from_record,
        to_record=args.to_record,
        all=args.all,
    )
    renderer.render(records)


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.add_argument(
        "--from",
        type=id_or_date,
        metavar="ID_OR_DATE",
        dest="from_record",
        help="The first story record to start logging from. "
        "Can be a date or ID. The date doesn't have to point "
        "to a specific record, anything from that point on "
        "will be included in the output. Note that for IDs "
        "validity isn't checked and will result in an empty "
        "output on improper use.",
    )
    parser.add_argument(
        "--to",
        type=id_or_date,
        metavar="ID_OR_DATE",
        dest="to_record",
        help="The last story record to include in the output. "
        "Can be a date or ID. The date doesn't have to point "
        "to specific record, anything up until that date will "
        "be included in the output. Note that for IDs validity "
        "isn't checked and will result in an empty output on "
        "improper use.",
    )
    parser.add_argument(
        "-c",
        "--changes",
        nargs="+",
        choices=CHANGES,
        action=UniqueChoices,
        default=CHANGES,
        help="A list of changes to display. By default all of them "
        "are displayed.",
    )
    parser.add_argument(
        "--username",
        help="Filter the output by username. That means displaying "
        "only updates that involve a specific user",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all story records in the output even if no "
        "updates occurred in between.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="When activated new records will be fetched online "
        "and will be included in the output",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Display the full username list in the output for "
        "each change and not just the number of updates",
    )
    parser.set_defaults(subfunc=run)
