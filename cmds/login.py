from argparse import ArgumentParser, Namespace
from .utils.bots import Bot


def run(args: Namespace):
    Bot.get(args.name, args.password, args.tfa_seed).login()


def setup_parser(parser: ArgumentParser):
    parser.set_defaults(func=run)
