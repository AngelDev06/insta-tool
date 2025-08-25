from datetime import datetime

from pydantic import BaseModel, field_serializer


class Viewer(BaseModel):
    """Instead of just the name we also keep track of when was the viewer first spotted in order to build a proper timeline.
    This object will be used by both cached and fetched entries."""

    name: str
    recorded_at: datetime

    @field_serializer("recorded_at")
    def serialize_recorded_at(self, recorded_at: datetime, _info):
        return recorded_at.timestamp()
