from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from ..models import cached
from ..utils.bots import Bot
from ..utils.renderers import StoryViewersRenderer
from ..utils.streams import ColoredOutput


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    args.name = bot.username

    records = cached.StoryHistory.get(args.name)
    renderer = StoryViewersRenderer(
        out=ColoredOutput(args.out, "green"), summary=args.summary
    )
    renderer.render(args.sid, records.stories.get(args.sid))


def setup_parser(parser: ArgumentParser):
    parser.add_argument("sid", type=int, metavar="story-id", help="The id of the story")
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display only the number of viewers, not the full list",
    )
    parser.set_defaults(subfunc=run)
