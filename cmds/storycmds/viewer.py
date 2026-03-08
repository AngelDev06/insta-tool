from argparse import ArgumentParser

from .viewercmds import add


def setup_parser(parser: ArgumentParser) -> None:
    operations = parser.add_subparsers(
        title="operations",
        required=True,
        help="operations for modifying a story's viewer history",
    )
    add.setup_parser(
        operations.add_parser(
            "add", help="Add one or more viewers to the record for a specific story"
        )
    )
    parser.set_defaults(subfunc=lambda args: args.subfunc2(args))
