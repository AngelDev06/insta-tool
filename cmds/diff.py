from argparse import ArgumentParser
from .diffcmds import lists, records


def setup_parser(parser: ArgumentParser):
    categories = parser.add_subparsers(
        title="categories",
        required=True,
        help="Select the type of diff to perform",
    )
    lists.setup_parser(
        categories.add_parser(
            "lists",
            help="Diff two lists of the same record "
            "(i.e. followers with followings or vise versa)",
        )
    )
    records.setup_parser(
        categories.add_parser(
            "records",
            help="Diff two records (i.e. two points in history) to "
            "determine which followers/followings were added/removed",
        )
    )
    parser.set_defaults(func=lambda args: args.subfunc(args))
