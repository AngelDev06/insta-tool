from __future__ import annotations

import json
import logging
import os
from base64 import b64decode
from typing import TYPE_CHECKING, Optional, TypedDict

from .tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client


class Config(TypedDict):
    name: str
    password: str


def get_credentials(name: Optional[str], password: Optional[str]) -> tuple[str, str]:
    if name is not None and password is not None:
        return name, password

    if not os.path.isfile("config.json"):
        logger.critical("no credentials specified and `config.json` is missing")
        raise RuntimeError("missing credentials")

    with open("config.json", encoding="utf-8") as file:
        data: Config = json.load(file)

    for param in ("name", "password"):
        if locals()[param] is not None:
            continue
        if param not in data:
            logger.critical(f"user {param} is missing from `config.json`")
            raise RuntimeError("corrupted config file")

        if param == "password":
            password = b64decode(data["password"]).decode()
        else:
            name = data["name"]

    return name, password


def _setup_insta_logger():
    from instagrapi import Client

    Client.public_request_logger.addHandler(logging.FileHandler("insta.log"))


def login(name: Optional[str], password: Optional[str]) -> Client:
    from instagrapi import Client

    name, password = get_credentials(name, password)
    client = Client()
    _setup_insta_logger()

    if not os.path.exists("session.json"):
        logger.debug("no session was found, attempting manual login...")
        if not client.login(name, password):
            logger.critical("failed to login")
            exit(1)

        logger.info(f"logged in as: {client.username}")
        client.dump_settings("session.json")
        client.delay_range = [1, 3]
        return client

    logger.debug("trying login with previous session")
    session = client.load_settings("session.json")

    client.set_settings(session)
    client.login(name, password)

    try:
        client.get_timeline_feed()
    except Exception:
        logger.debug(
            "failed to login using the previous session, attempting manual login..."
        )

        if not client.login(name, password, relogin=True):
            logger.exception("failed to login")
            exit(1)

        client.dump_settings("session.json")
        client.relogin_attempt -= 1

    logger.info(f"logged in as: {client.username}")
    client.delay_range = [1, 3]
    return client
