from argparse import ArgumentParser
from .logcmds import delete, show, reset


def setup_parser(parser: ArgumentParser) -> None:
    operations = parser.add_subparsers(
        title="operations", required=True, help="Log based operations"
    )
    show.setup_parser(
        operations.add_parser(
            "show",
            help="Display records of a specific user (with optional filters)",
        )
    )
    delete.setup_parser(
        operations.add_parser(
            "delete",
            help="Delete a record from a user (further modifications "
            "will also be made to prevent corruption by default)",
        )
    )
    reset.setup_parser(
        operations.add_parser(
            "reset",
            help="Reset all records up to a specific date (meaning "
            "any record after that date will be reverted and removed "
            "permanently)",
        )
    )
    parser.set_defaults(func=lambda args: args.subfunc(args))
