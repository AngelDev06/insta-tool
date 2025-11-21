from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_serializer, field_validator

from ..utils.constants import DATE_OUTPUT_FORMAT


class Viewer(BaseModel):
    """Instead of just the name we also keep track of when was the viewer first spotted in order to build a proper timeline.
    This object will be used by both cached and fetched entries."""

    name: str
    recorded_at: datetime

    @field_serializer("recorded_at")
    def serialize_recorded_at(self, recorded_at: datetime, _info):
        return recorded_at.timestamp()

    @field_validator("recorded_at", mode="before")
    @classmethod
    def validate_recorded_at(cls, recorded_at: Any) -> datetime:
        if isinstance(recorded_at, str):
            return datetime.strptime(recorded_at, DATE_OUTPUT_FORMAT)
        if isinstance(recorded_at, float):
            return datetime.fromtimestamp(recorded_at)
        raise TypeError("invalid type of timestamp")

    def __str__(self) -> str:
        return f"{self.name} ({self.recorded_at.strftime(DATE_OUTPUT_FORMAT)})"
