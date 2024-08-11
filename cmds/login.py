from argparse import ArgumentParser, Namespace

from .utils.login import login


def run(args: Namespace):
    login(args.name, args.password)


def setup_parser(parser: ArgumentParser):
    parser.set_defaults(func=run)
