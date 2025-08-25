from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from .models import cached
from .utils.filters import list_filter
from .utils.parsers import date_parser
from .utils.renderers import UsersDiffRenderer, UsersDiffRendererData
from .utils.streams import ColoredOutput


def get_comparison_type(args: Namespace):
    if args.diff:
        return "diff"
    if args.mutuals:
        return "mutuals"
    return "both"


def run(args: Namespace):
    lists = list_filter(args)
    cached1 = cached.User.get(args.user1)
    cached2 = cached.User.get(args.user2)

    user1 = (
        cached1.checkout(args.record1, lists) if args.record1 is not None else cached1
    )
    user2 = (
        cached2.checkout(args.record2, lists) if args.record2 is not None else cached2
    )

    renderer = UsersDiffRenderer(
        ColoredOutput(args.out, "green"),
        lists=lists,
        detailed=not args.summary,
        user1=UsersDiffRendererData(name=args.user1, date=args.record1, data=user1),
        user2=UsersDiffRendererData(name=args.user2, date=args.record2, data=user2),
        comparison_type=get_comparison_type(args),
    )
    renderer.render()


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
        "-r1",
        "--record1",
        type=date_parser,
        help="The date of the first user's record to base comparison on (defaults to latest if not provided)",
    )
    parser.add_argument(
        "-r2",
        "--record2",
        type=date_parser,
        help="The date of the second user's record to base comparison on (defaults to latest if not provided)",
    )
    parser.add_argument(
        "--list",
        choices=("followers", "followings"),
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
