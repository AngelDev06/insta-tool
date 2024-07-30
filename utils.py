import logging
from ensta import Web
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

def login(name: str, password: Optional[str]) -> Web:
    logger = logging.getLogger("insta-tool-logger")
    logger.info(f"logging in as: {name}")
    if not password:
        with open("ps.txt", "rb") as file:
            password = b64decode(file.read()).decode("utf-8")
    return Web(name, password)
