from utils import login
from argparse import ArgumentParser, Namespace


def run(args: Namespace):
    login(args.name, args.password)


def setup_parser(parser: ArgumentParser):
    parser.set_defaults(func=run)
