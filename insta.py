from argparse import ArgumentParser

from cmds import diff, login, log, checkout, compare, state, listbots
from cmds.utils.tool_logger import setup as setup_logger


def main():
    parser = ArgumentParser(
        prog="insta",
        description="A tool for interacting with the instagram api",
    )
    parser.add_argument(
        "--name",
        help="The name of the account to login",
    )
    parser.add_argument(
        "--password",
        "--pass",
        help="The password of the account to login",
    )
    parser.add_argument(
        "-2fa",
        "--2fa-seed",
        dest="tfa_seed",
        help="The 2fa seed to generate codes from (if required)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(
        title="Subcommands",
        required=True,
        help="The subcommands provided by the tool",
    )
    diff.setup_parser(
        subparsers.add_parser(
            "diff",
            help="Checks for any updates to an account since the last time it was cached",
        )
    )
    login.setup_parser(
        subparsers.add_parser(
            "login", help="Tries to login and updates the session info"
        )
    )
    log.setup_parser(
        subparsers.add_parser(
            "log",
            help="Logs a user's scan history (from most recent to oldest)",
        )
    )
    checkout.setup_parser(
        subparsers.add_parser(
            "checkout",
            help="Reconstruct history (i.e. followers/followings list) of a user "
            "at a specific point in time based on the changelog available",
        )
    )
    state.setup_parser(
        subparsers.add_parser(
            "state",
            help="Effectively a checkout to the currently cached state of "
            "followers/followings or a dynamically fetched one",
        )
    )
    compare.setup_parser(
        subparsers.add_parser(
            "compare",
            help="Provides comparison information between two user records "
            "(this only operates on cache, i.e. it does not dynamically fetch information)"
            "(i.e. mutual followers/followings or differences)",
        )
    )
    listbots.setup_parser(
        subparsers.add_parser(
            "listbots", help="List all of the currently configured bots"
        )
    )

    args = parser.parse_args()
    setup_logger(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
