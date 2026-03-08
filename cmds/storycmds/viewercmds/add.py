from argparse import ArgumentParser, Namespace
from datetime import datetime

from termcolor import cprint

from ...models import cached
from ...models.viewer import Viewer
from ...utils.bots import Bot
from ...utils.parsers import username_with_id
from ...utils.uids import UIDMap


def run(args: Namespace) -> None:
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    args.name = bot.username

    records = cached.StoryHistory.get(args.name)
    story = records.stories.get(args.sid)

    if story is None:
        cprint("story with specified id was not found in the records", "red")
        return

    for uid, name in args.viewers:
        if not uid:
            uid = records.lookup_uid(name)
            if not uid:
                cprint(
                    f"Viewer with name {name} could not be added as their id was not found in records",
                    "red",
                    attrs=("bold", "underline"),
                )
                continue

        story.viewers[uid] = Viewer.model_construct(
            name=name, recorded_at=datetime.now()
        )
        cprint(
            f"Viewer with name {name} was added successfully",
            "green",
            attrs=("bold", "underline"),
        )

    records.dump(args.name, UIDMap.get().uid_of(args.name))


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "sid", type=int, metavar="story-id", help="The id of the story to modify"
    )
    parser.add_argument(
        "viewers",
        type=username_with_id,
        nargs="+",
        help="The viewers' usernames to register. Each entry can be associated with an id in the format <name>-<id> in case the tool can't find their id in records",
    )
    parser.set_defaults(subfunc2=run)
