from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_serializer

from ..utils.constants import DATE_OUTPUT_FORMAT
from ..utils.scrapping import Scrapper
from ..utils.tool_logger import logger

if TYPE_CHECKING:
    from instagrapi import Client
    from instagrapi.types import Story as InstaStory


class ViewersUpdate(BaseModel):
    story_timestamp: datetime
    added: dict[int, Viewer]
    removed: dict[int, Viewer]
    renamed: dict[int, tuple[Viewer, Viewer]]

    @field_serializer("story_timestamp")
    def serialize_story_timestamp(self, story_timestamp: datetime, _info):
        return story_timestamp.timestamp()


class CachedStoryHistory(BaseModel):
    last_viewer_list: dict[int, Viewer] = Field(default_factory=dict)
    stories_changelog: dict[int, ViewersUpdate] = Field(default_factory=dict)
