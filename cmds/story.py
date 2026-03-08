from argparse import ArgumentParser

from .storycmds import diff, listcmd, log, lookup, viewer


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
    diff.setup_parser(
        operations.add_parser(
            "diff",
            help="Compare two story records (i.e. the full viewer lists) "
            "to determine the updates that occurred between them (e.g. "
            "added/removed viewers)",
        )
    )
    log.setup_parser(
        operations.add_parser(
            "log",
            help="Log viewer changelog (e.g. added/removed viewers) "
            "throughout the story history that is available",
        )
    )
    viewer.setup_parser(
        operations.add_parser(
            "viewer",
            help="Story viewer history modification tools such as adding new viewers manually or removing them",
        )
    )
    parser.set_defaults(func=lambda args: args.subfunc(args))
