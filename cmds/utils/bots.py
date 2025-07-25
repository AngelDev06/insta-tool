from __future__ import annotations
import logging
from pydantic import BaseModel, field_serializer, field_validator, Field
from base64 import b64decode, b64encode
from typing import Optional, cast, TYPE_CHECKING
from .tool_logger import logger
from .uids import UIDMap
from .constants import CONFIG_FOLDER, SESSIONS_FOLDER

if TYPE_CHECKING:
    from instagrapi import Client

_config: Optional[Config] = None


class Bot(BaseModel):
    username: str
    password: str
    tfa_seed: Optional[str] = None

    @classmethod
    def get(
        cls,
        username: Optional[str] = None,
        password: Optional[str] = None,
        tfa_seed: Optional[str] = None,
    ):
        if username is not None and password is not None:
            return cls.model_construct(
                username=username, password=password, tfa_seed=tfa_seed
            )
        return Config.get().get_bot(username)

    def try_session_login(self, client: Client) -> bool:
        uid = UIDMap.get().uid_of(self.username)
        if uid is None:
            return False
        session_path = SESSIONS_FOLDER / f"{uid}.json"
        if not session_path.is_file():
            return False

        logger.debug("trying login with previous session...")
        session = client.load_settings(session_path)
        client.set_settings(session)
        client.login(self.username, self.password)

        try:
            client.get_timeline_feed()
        except Exception:
            logger.debug(
                "failed to login using the previous session, attempting manual login..."
            )

            if not client.login(
                self.username,
                self.password,
                relogin=True,
                verification_code=self.tfa_code,
            ):
                logger.exception("failed to login")
                raise RuntimeError("manual login failed")

            client.dump_settings(session_path)
            client.relogin_attempt -= 1
        return True

    def login(self):
        from instagrapi import Client

        client = Client()
        Client.public_request_logger.addHandler(
            logging.FileHandler("insta.log")
        )

        if not self.try_session_login(client):
            logger.debug("no session was found, attempting manual login...")
            if not client.login(
                self.username, self.password, verification_code=self.tfa_code
            ):
                logger.critical("failed to login")
                raise RuntimeError("manual login failed")
            UIDMap.get().add_entry(cast(str, client.username), client.user_id)
            if not SESSIONS_FOLDER.is_dir():
                SESSIONS_FOLDER.mkdir()
            client.dump_settings(SESSIONS_FOLDER / f"{client.user_id}.json")

        logger.info(f"logged in as: {client.username}")
        client.delay_range = [1, 3]

        Config.get().add_entry(client.user_id, self)
        return client

    @property
    def tfa_code(self):
        from instagrapi import Client

        if self.tfa_seed is not None:
            return Client.totp_generate_code(self.tfa_seed)
        return ""

    @field_validator("password")
    @staticmethod
    def decode_password(value: str) -> str:
        return b64decode(value).decode()

    @field_serializer("password")
    def encode_password(self, password: str, _info) -> str:
        return b64encode(password.encode()).decode()


class Config(BaseModel):
    current_uid: Optional[int] = None
    bots: dict[int, Bot] = Field(default_factory=dict)

    @classmethod
    def get(cls):
        global _config
        if _config is not None:
            return _config
        config_file = CONFIG_FOLDER / "config.json"
        if not config_file.is_file():
            _config = cls()
        else:
            with open(config_file, encoding="utf-8") as file:
                _config = cls.model_validate_json(file.read())
        return _config

    def backup(self):
        if not CONFIG_FOLDER.is_dir():
            CONFIG_FOLDER.mkdir()
        config_file = CONFIG_FOLDER / "config.json"
        with open(config_file, "w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=2))

    @property
    def current_bot(self) -> Bot:
        if self.current_uid is None:
            logger.critical(
                f"no bot is currently configured for id `{self.current_uid}`"
            )
            raise RuntimeError("missing configuration")
        return self.bots[self.current_uid]

    def get_bot_by_name(self, username: str) -> Bot:
        uid = UIDMap.get().uid_of(username)
        if uid is None:
            logger.critical(
                f"no configuration is associated for bot with name: {username}"
            )
            raise RuntimeError("missing configuration")
        self.current_uid = uid
        self.backup()
        return self.current_bot

    def get_bot(self, username: Optional[str] = None) -> Bot:
        if username is not None:
            return self.get_bot_by_name(username)
        return self.current_bot

    def add_entry(self, uid: int, bot: Bot, backup: bool = True):
        self.current_uid = uid
        cached = self.bots.get(uid)
        if cached is not None and cached == bot:
            return
        self.bots[uid] = bot
        if backup:
            self.backup()
