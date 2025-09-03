from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from .models import cached
from .utils.actions import UniqueChoices
from .utils.parsers import date_parser
from .utils.renderers import UsersDiffRenderer, UsersDiffRendererData
from .utils.streams import ColoredOutput
from .utils.constants import LISTS


def get_comparison_type(args: Namespace):
    if args.diff:
        return "diff"
    if args.mutuals:
        return "mutuals"
    return "both"


def run(args: Namespace):
    renderer = UsersDiffRenderer(
        out=ColoredOutput(args.out, "green"),
        lists=args.lists,
        username=args.username,
        detailed=not args.summary,
        comparison_type=get_comparison_type(args),
    )
    cached1 = cached.User.get(args.user1)
    cached2 = cached.User.get(args.user2)

    user1 = (
        cached1.checkout(args.state1, args.lists)
        if args.state1 is not None
        else cached1
    )
    user2 = (
        cached2.checkout(args.state2, args.lists)
        if args.state2 is not None
        else cached2
    )
    renderer.render(
        UsersDiffRendererData(args.user1, args.state1, user1),
        UsersDiffRendererData(args.user2, args.state2, user2),
    )


def setup_parser(parser: ArgumentParser):
    parser.add_argument("user1", help="The name of the first user to compare")
    parser.add_argument("user2", help="The name of the second user to compare")
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the result to",
    )
    parser.add_argument(
        "-s1",
        "--state1",
        type=date_parser,
        metavar="DATE",
        help="The date of the first user's state to base comparison on (defaults to "
        "latest if not provided). No updates that happened in the date specified are included.",
    )
    parser.add_argument(
        "-s2",
        "--state2",
        type=date_parser,
        metavar="DATE",
        help="The date of the second user's state to base comparison on (defaults to "
        "latest if not provided). No updates that happened in the date specified are included.",
    )
    parser.add_argument(
        "--lists",
        nargs="+",
        choices=LISTS,
        action=UniqueChoices,
        default=LISTS,
        help="An option to choose which list's comparison "
        "results will be displayed (if not provided, both lists are displayed)",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--diff",
        action="store_true",
        help="Show just the differences in followers/followings between the two accounts",
    )
    group.add_argument(
        "--mutuals",
        action="store_true",
        help="Show only the followers/followings the two accounts have in common (mutuals)",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display a shorter version with just the count of users instead of the full list",
    )
    parser.set_defaults(func=run)
