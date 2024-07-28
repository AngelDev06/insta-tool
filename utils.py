import os
import logging
import json
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from base64 import b64decode
from typing import Optional
from termcolor import cprint
from pathlib import Path

class Writer:
    def __init__(self, file: Optional[Path]):
        self.file = None
        if file:
            self.file = open(file, "w", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.file:
            self.file.close()

    def print(self, text: str):
        if self.file:
            self.file.write(text)
            self.file.write('\n')
            return
        cprint(text, "green", attrs=["bold", "underline"])

def login(name: str, password: Optional[str]) -> Client:
    logger = logging.getLogger("insta-tool-logger")
    client = Client()
    logger.info(f"logging in with username: {name}")
    
    if not password:
        with open("ps.txt", "rb") as file:
            password = b64decode(file.read()).decode("utf-8")

    if not os.path.exists("session.json"):
        logger.info(
            "no previous session was found, attempting manual login...")
        if not client.login(name, password):
            logger.critical("failed to login")
            exit(1)
        logger.info("successfully logged in")
        client.dump_settings("session.json")
    else:
        logger.info("previous session was found, using it to login...")
        session = client.load_settings("session.json")

        try:
            client.set_settings(session)
            client.login(name, password)

            try:
                client.get_timeline_feed()
            except LoginRequired:
                logger.error(
                    "previous session is invalid, attempting re-login")
                old_session = client.get_settings()
                client.set_settings({})
                client.set_uuids(old_session["uuids"])
                client.login(name, password)
                client.dump_settings("session.json")
            logger.info("successfully logged in via session")
        except Exception:
            logger.exception(
                "login with session failed, attempting manual login")

            if not client.login(name, password, relogin=True):
                logger.critical("failed to login")
                exit(1)
            logger.info("successfully logged in manually")
            client.dump_settings("session.json")
    return client

def get_cache():
    if not os.path.exists("cache.json"):
        default = {"analyse": {}}
        with open("cache.json", "w", encoding="utf-8") as cache:
            json.dump(default, cache, indent=2)
        return default
    with open("cache.json", encoding="utf-8") as cache:
        return json.load(cache)

def update_cache(data):
    with open("cache.json", "w", encoding="utf-8") as cache:
        json.dump(data, cache, indent=2)
