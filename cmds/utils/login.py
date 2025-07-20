from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional, cast, NoReturn
from .tool_logger import logger
from .constants import SESSIONS_FOLDER, CONFIG_PATH
from .uids import get_uid_table, store_uid
from .config import BotConfig

if TYPE_CHECKING:
    from instagrapi import Client


def error_missing_credentials() -> NoReturn:
    logger.critical("no credentials specified and configuration is missing")
    raise RuntimeError("missing credentials")


def get_credentials(
    name: Optional[str], password: Optional[str]
) -> tuple[str, str]:
    if name is not None and password is not None:
        return name, password
    
    recent_config_path = CONFIG_PATH / "recent.txt"
    if name is None:
        if not recent_config_path.is_file():
            error_missing_credentials()
        with open(recent_config_path) as file:
            uid = int(file.read())
        should_set_recent = False
    else:
        uids = get_uid_table()
        if name not in uids:
            error_missing_credentials()
        uid = uids[name]
        should_set_recent = True

    config_path = CONFIG_PATH / f"{uid}.json"
    if not config_path.is_file():
        error_missing_credentials()

    with open(config_path, encoding="utf-8") as file:
        bot = BotConfig.model_validate_json(file.read())
    
    if should_set_recent:
        with open(recent_config_path, "w") as file:
            file.write(str(uid))
    return bot.username, bot.password


def _setup_insta_logger():
    from instagrapi import Client

    Client.public_request_logger.addHandler(logging.FileHandler("insta.log"))


def try_session_login(client: Client, name: str, password: str) -> bool:
    uids = get_uid_table()
    if name not in uids:
        return False
    uid = uids[name]
    session_path = SESSIONS_FOLDER / f"{uid}.json"
    if not session_path.is_file():
        return False

    logger.debug("trying login with previous session...")
    session = client.load_settings(session_path)
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
            raise RuntimeError("manual login failed")

        client.dump_settings(session_path)
        client.relogin_attempt -= 1
    return True


def login(name: Optional[str], password: Optional[str]) -> Client:
    from instagrapi import Client

    should_configure = name is not None and password is not None
    name, password = get_credentials(name, password)
    client = Client()
    _setup_insta_logger()

    if not try_session_login(client, name, password):
        logger.debug("no session was found, attempting manual login...")
        if not client.login(name, password):
            logger.critical("failed to login")
            raise RuntimeError("manual login failed")
        store_uid(cast(str, client.username), client.user_id)
        if not SESSIONS_FOLDER.is_dir():
            SESSIONS_FOLDER.mkdir()
        client.dump_settings(SESSIONS_FOLDER / f"{client.user_id}.json")

    logger.info(f"logged in as: {client.username}")
    client.delay_range = [1, 3]

    if should_configure:
        bot = BotConfig.model_construct(username=name, password=password)
        if not CONFIG_PATH.is_dir():
            CONFIG_PATH.mkdir()
        with open(
            CONFIG_PATH / f"{client.user_id}.json", "w", encoding="utf-8"
        ) as file:
            file.write(bot.model_dump_json(indent=2))
        with open(CONFIG_PATH / "recent.txt", "w") as file:
            file.write(str(client.user_id))
    return client
