import json
from base64 import b64encode
from argparse import ArgumentParser, Namespace

def run(args: Namespace):
    with open("config.json", "w", encoding="utf-8") as file:
        data = {"name": args.name, "password": b64encode(args.password.encode()).decode()}
        json.dump(data, file, indent=2)

def setup_parser(parser: ArgumentParser):
    parser.add_argument("name", help="The account name")
    parser.add_argument("password", help="The account password")
    parser.set_defaults(func=run)
