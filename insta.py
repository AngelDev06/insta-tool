from argparse import ArgumentParser

import analyse
import config
import login
from tool_logger import setup as setup_logger


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
        help="The password for the account to login (if omitted b64 decodes the contents of `ps.txt`)",
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
            help="Fetches all followers and following from the target and determines which of them don't follow back",
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
