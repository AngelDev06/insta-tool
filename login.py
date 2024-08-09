import json
import logging
import os
from base64 import b64decode
from instagrapi import Client
from argparse import ArgumentParser, Namespace
from typing import Optional, Literal

logger = logging.getLogger("insta-tool-logger")

def _get_credentials(name: Optional[str], password: Optional[str]) -> tuple[str, str]:
    if name is not None and password is not None:
        return name, password

    if not os.path.isfile("config.json"):
        logger.critical(
            "no credentials specified and `config.json` is missing"
        )
        exit(1)

    with open("config.json", encoding="utf-8") as file:
        data: dict[Literal["name", "password"], str] = json.load(file)
        
    for param in ("name", "password"):
        if locals()[param] is not None:
            continue
        if param not in data:
            logger.critical(f"user {param} is missing from `config.json`")
            exit(1)

        locals()[param] = data[param]
        if param == "password":
            password = b64decode(password).decode()

    return name, password


def login(name: Optional[str], password: Optional[str]) -> Client:
    name, password = _get_credentials(name, password)
    logger.info(f"logging in as: {name}")
    client = Client()

    if not os.path.exists("session.json"):
        logger.debug("no session was found, attempting manual login...")
        if not client.login(name, password):
            logger.critical("failed to login")
            exit(1)

        logger.info(f"logged in as: {client.username}")
        return client

    logger.debug("trying login with previous session")
    session = client.load_settings("session.json")

    client.set_settings(session)
    client.login(name, password)

    try:
        client.get_timeline_feed()
    except Exception:
        logger.debug("failed to login using the previous session, attempting manual login...")

        if not client.login(name, password, relogin=True):
            logger.exception("failed to login")
            exit(1)

        client.dump_settings("session.json")
        client.relogin_attempt -= 1
    
    logger.info(f"logged in as: {client.username}")
    return client


def run(args: Namespace):
    login(args.name, args.password)


def setup_parser(parser: ArgumentParser):
    parser.set_defaults(func=run)
