import logging
import os
from base64 import b64decode
from sys import argv
from time import sleep

from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from instagrapi.exceptions import PleaseWaitFewMinutes
from termcolor import colored
from termcolor import cprint


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "red",
        logging.INFO: "blue",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "light_red"
    }

    def format(self, record: logging.LogRecord):
        return colored(super().format(record), self.COLORS[record.levelno])


logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter(fmt="[%(levelname)s] (%(asctime)s) %(name)s: %(message)s",
                     datefmt="%d/%m/%Y %H:%M:%S"))
logger.addHandler(handler)


def login() -> Client:
    client = Client()
    username = "angel.tserk"
    logger.info(f"logging in with username: {username}")

    with open("ps.txt", "rb") as file:
        password = b64decode(file.read()).decode("utf-8")

    if not os.path.exists("session.json"):
        logger.info(
            "no previous session was found, attempting manual login...")
        if not client.login(username, password):
            logger.critical("failed to login")
            exit(1)
        logger.info("successfully logged in")
        client.dump_settings("session.json")
    else:
        logger.info("previous session was found, using it to login...")
        session = client.load_settings("session.json")

        try:
            client.set_settings(session)
            client.login(username, password)

            try:
                client.get_timeline_feed()
            except LoginRequired:
                logger.error(
                    "previous session is invalid, attempting re-login")
                old_session = client.get_settings()
                client.set_settings({})
                client.set_uuids(old_session["uuids"])
                client.login(username, password)
                client.dump_settings("session.json")
            logger.info("successfully logged in via session")
        except Exception:
            logger.exception(
                "login with session failed, attempting manual login")

            if not client.login(username, password):
                logger.critical("failed to login")
                exit(1)
            logger.info("successfully logged in manually")
            client.dump_settings("session.json")
    return client


def main():
    client = login()
    client.delay_range = [1, 3]

    user_id = client.user_id if len(
        argv) == 1 else client.user_id_from_username(argv[1])
    followers_usernames = {
        follower.username
        for follower in client.user_followers(user_id).values()
    }

    logger.info("fetched followers")

    while True:
        try:
            following_usernames = {
                following.username
                for following in client.user_following(user_id).values()
            }

            logger.info("fetched following")
            break
        except PleaseWaitFewMinutes:
            logger.exception("got rate limited, sleeping for 2 minutes...")
            sleep(120)
            logger.info("retrying fetching...")

    for following_username in following_usernames.difference(
            followers_usernames):
        cprint(following_username, "green", attrs=["bold", "underline"])


if __name__ == "__main__":
    main()
