from argparse import ArgumentParser

from .storycmds import listcmd, lookup


def setup_parser(parser: ArgumentParser):
    operations = parser.add_subparsers(
        title="operations",
        required=True,
        help="Story viewers related operations",
        description="All of these commands use the bot itself as the "
        "target account (whose stories and viewers list will be fetched) "
        "since viewers are only accessible by the story uploader. "
        "So access to the uploader's account is required in this case.",
    )
    lookup.setup_parser(
        operations.add_parser(
            "lookup",
            help="Lookup which of the recorded (or fetched) stories a specific user appear to have watched",
        )
    )
    listcmd.setup_parser(
        operations.add_parser(
            "list", help="List the viewers of a story specified by id"
        )
    )
    parser.set_defaults(func=lambda args: args.subfunc(args))
