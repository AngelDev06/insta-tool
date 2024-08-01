import json
import logging
import os
from base64 import b64decode
from ensta import Web
from argparse import ArgumentParser, Namespace
from typing import Optional, Literal

logger = logging.getLogger("insta-tool-logger")


def login(name: Optional[str], password: Optional[str]) -> Web:
    if not name or not password:
        if not os.path.isfile("config.json"):
            logger.critical(
                "no credentials specified and `config.json` is missing"
            )
            exit(1)
        with open("config.json", encoding="utf-8") as file:
            data: dict[Literal["name", "password"], str] = json.load(file)
            if not name:
                if "name" not in data:
                    logger.critical("user name is missing from `config.json`")
                    exit(1)
                name = data["name"]
            if not password:
                if "password" not in data:
                    logger.critical(
                        "user password is missing from `config.json`"
                    )
                    exit(1)
                password = b64decode(data["password"]).decode()
    
    logger.info(f"logging in as: {name}")
    return Web(name, password)


def run(args: Namespace):
    client = login(args.name, args.password)
    logger.info(f"successfully logged in as: {client.username}")


def setup_parser(parser: ArgumentParser):
    parser.set_defaults(func=run)
