from argparse import ArgumentParser, FileType, Namespace
from sys import stdout
from itertools import dropwhile
from typing import Optional, Union, overload, NoReturn
from datetime import date

from ..utils.constants import CHANGES
from ..utils.actions import UniqueChoices
from ..utils.parsers import id_or_date
from ..utils.tool_logger import logger
from ..utils.renderers import ViewersDiffRenderer
from ..utils.bots import Bot
from ..utils.streams import ColoredOutput
from ..models import cached, fetched


@overload
def verify_story_access(
    parser: ArgumentParser,
    story: None,
    sid_or_date: Union[int, date],
    story_text: str,
) -> NoReturn: ...


@overload
def verify_story_access(
    parser: ArgumentParser,
    story: cached.Story,
    sid_or_date: Union[int, date],
    story_text: str,
) -> None: ...


def verify_story_access(
    parser: ArgumentParser,
    story: Optional[cached.Story],
    sid_or_date: Union[int, date],
    story_text: str,
):
    if story is not None:
        return
    if isinstance(sid_or_date, int):
        parser.error(f"invalid story id given for the {story_text}")
    parser.error(
        f"no story exists for the {story_text} at date specified in record"
    )


def get_last_value[T1, T2](data: dict[T1, T2]) -> T2:
    return next(
        dropwhile(
            lambda item: item[0] != len(data), enumerate(data.values(), 1)
        )
    )[1]


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    args.name = bot.username

    records = cached.StoryHistory.get(args.name)
    if not records.stories:
        logger.critical(
            "There are no stories in record for the user specified"
        )
        return

    if args.story1 is None:
        story1 = get_last_value(records.stories)
    else:
        _, story1 = records.at(args.story1)
        verify_story_access(
            args.diffparser, story1, args.story1, "first story"
        )

    if args.story2 is None:
        client = bot.login()
        stories = fetched.Stories.fetch(client, args.name, args.chunk_size)
        if not stories:
            logger.critical(
                "no stories received from the api so nothing to compare"
            )
            return
        story2 = get_last_value(stories.stories)
    else:
        _, story2 = records.at(args.story2)
        verify_story_access(
            args.diffparser, story2, args.story2, "second story"
        )

    renderer = ViewersDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        changes=args.changes,
        username=args.username,
        detailed=not args.summary,
    )
    renderer.render(story1, story2)


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "story1",
        nargs="?",
        type=id_or_date,
        metavar="first-story",
        help="First date (DD-MM-YYYY) of story record to use. "
        "When more than one story share the same date, the "
        "oldest one is used (if none do an error is produced). "
        "If not specified, defaults to the last story recorded. "
        "The story id can also be specified directly.",
    )
    parser.add_argument(
        "story2",
        nargs="?",
        type=id_or_date,
        metavar="second-story",
        help="End date (DD-MM-YYYY) of story record to use. "
        "When more than one story share the same date, the "
        "most recent one is used (if none do an error is "
        "produced). If not specified, defaults to fetching "
        "from instagram (if multiple stories are fetched, "
        "the most recent one is used). The story id can "
        "also be specified directly.",
    )
    parser.add_argument(
        "--username", help="Only show updates for a specific user"
    )
    parser.add_argument(
        "-c",
        "--changes",
        nargs="+",
        choices=CHANGES,
        action=UniqueChoices,
        default=CHANGES,
        help="Display only specific changes",
    )
    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Display a shorter version (i.e. just the number of viewer updates, not the full list)",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result",
    )
    parser.set_defaults(subfunc=run, diffparser=parser)
