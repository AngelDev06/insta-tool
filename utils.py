import logging
import os
import json
from ensta import Web
from base64 import b64decode
from typing import Optional, Literal
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
            self.file.write("\n")
            return
        cprint(text, "green", attrs=["bold", "underline"])


def login(name: Optional[str], password: Optional[str]) -> Web:
    logger = logging.getLogger("insta-tool-logger")
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
    print(password)
    return Web(name, password)
