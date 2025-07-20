from pydantic import BaseModel, field_serializer, field_validator
from base64 import b64decode, b64encode


class BotConfig(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @staticmethod
    def decode_password(value: str) -> str:
        return b64decode(value).decode()

    @field_serializer("password")
    def encode_password(self, password: str, _info) -> str:
        return b64encode(password.encode()).decode()
