from argparse import ArgumentParser, Namespace
from termcolor import cprint
from ..utils.parsers import date_parser
from ..models import cached


def run(args: Namespace) -> None:
    cached_user = cached.User.get(args.target)

    if not cached_user:
        cprint("No logs available for the user specified", "red")
        return

    if cached_user.delete(args.target, args.record, args.hard):
        cprint(
            "Record was deleted successfully",
            "green",
            attrs=("bold", "underline"),
        )
    else:
        cprint("No record was deleted", "red", attrs=("bold", "underline"))


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "target", help="The target whose record will be deleted (not optional)"
    )
    parser.add_argument(
        "record",
        type=date_parser,
        metavar="record-date",
        help="The date (DD-MM-YYYY) of record to delete. "
        "If more than one exist for that date, live input "
        "will be provided to select",
    )
    parser.add_argument(
        "--hard",
        action="store_true",
        help="By default, upon deletion of a record the one that came after it "
        "(chronologically) is modified so that the rest of the history is left "
        "unaffected by the deletion. This option will force no modification to occur "
        "but can irreversibly corrupt the state history.",
    )
    parser.set_defaults(subfunc=run)
