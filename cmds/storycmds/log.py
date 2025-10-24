from argparse import ArgumentParser
from .logcmds import show, delete


def setup_parser(parser: ArgumentParser):
    operations = parser.add_subparsers(
        title="operations", required=True, help="Story log based operations"
    )
    show.setup_parser(
        operations.add_parser(
            "show",
            help="Show a list of stories in history in the form of viewer updates",
        )
    )
    delete.setup_parser(
        operations.add_parser(
            "delete",
            help="Delete a specific record either by a story ID or a date",
        )
    )
    parser.set_defaults(subfunc=lambda args: args.subfunc2(args))
