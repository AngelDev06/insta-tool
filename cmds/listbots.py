from sys import stdout
from argparse import ArgumentParser, Namespace, FileType
from typing import TextIO
from .utils.bots import Config


def run(args: Namespace):
    config = Config.get()
    out: TextIO = args.out

    if config.current_uid is not None:
        out.write(f"CURRENT BOT ID: {config.current_uid}\n\n")

    for uid, bot in config.bots.items():
        out.write("Bot:\n")
        out.write(f"  username: {bot.username}\n")
        out.write(f"  userid: {uid}\n")
        if args.show_password:
            out.write(f"  password: {bot.password}\n")
        out.write("\n")


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "out",
        type=FileType("w", encoding="utf-8"),
        nargs="?",
        default=stdout,
        help="An optional file to output the result",
    )
    parser.add_argument(
        "--show-password",
        action="store_true",
        help="Display each bot's password",
    )
    parser.set_defaults(func=run)
