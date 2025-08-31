from argparse import ArgumentParser, FileType, Namespace
from sys import stdout

from ..utils.constants import CHANGES


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "date1",
        nargs="?",
        metavar="first-date",
        help="First date (DD-MM-YYYY) of story record to use. "
        "When more than one story share the same date, the "
        "oldest one is used (if none do an error is produced). "
        "If not specified, defaults to the last story recorded",
    )
    parser.add_argument(
        "date2",
        nargs="?",
        metavar="second-date",
        help="End date (DD-MM-YYYY) of story record to use. "
        "When more than one story share the same date, the "
        "most recent one is used (if none do an error is "
        "produced). If not specified, defaults to fetching "
        "from instagram (if multiple stories are fetched, "
        "the most recent one is used)",
    )
    parser.add_argument("--username", help="Only show updates for a specific user")
    parser.add_argument(
        "-c", "--change", choices=CHANGES, help="Display only a specific change"
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
