from argparse import ArgumentParser

from cmds import analyse, config, diff, login
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
    analyse.setup_parser(
        subparsers.add_parser(
            "analyse",
            help="Fetches all followers and followings from the target and determines which of them don't follow back",
        )
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
    config.setup_parser(
        subparsers.add_parser("config", help="Configures the bot's account credentials")
    )

    args = parser.parse_args()
    setup_logger(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
