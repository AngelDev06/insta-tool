from argparse import ArgumentParser, Namespace
from termcolor import cprint
from ..utils.parsers import date_parser
from ..models import cached


def run(args: Namespace):
    cached_user = cached.User.get(args.target)

    if not cached_user:
        cprint(
            "No records exist for the user specified",
            "red",
            attrs=("bold", "underline"),
        )
        return
    cached_user.reset(args.target, args.date)
    cprint("Operation Finished", "green", attrs=("bold", "underline"))


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "target", help="The target whose state will be reset (not optional)"
    )
    parser.add_argument(
        "date",
        type=date_parser,
        help="The date based on which the state will be reset "
        "(any updates that happened in that date will also be reverted)",
    )
    parser.set_defaults(subfunc=run)
