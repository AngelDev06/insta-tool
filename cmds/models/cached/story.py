from datetime import date, datetime
from typing import ClassVar, Optional, Self, Union

from pydantic import BaseModel, Field, field_serializer

from .. import fetched, mixins
from ..viewer import Viewer


class Story(mixins.Story, BaseModel):
    timestamp: datetime
    viewers: dict[int, Viewer]

    @field_serializer("timestamp")
    def serialize_taken_at(self, timestamp: datetime, _info):
        return timestamp.timestamp()


class StoryHistory(mixins.Cached, BaseModel):
    subdir: ClassVar[str] = "stories"
    stories: dict[int, Story] = Field(default_factory=dict)

    def dump_update(self, fetched_stories: fetched.Stories) -> None:
        for story_id, story in fetched_stories:
            if story_id in self.stories:
                current = self.stories[story_id]
                current.viewers = story.viewers | current.viewers
            else:
                self.stories[story_id] = Story.model_construct(
                    timestamp=story.taken_at, viewers=story.viewers
                )

        self.dump(fetched_stories.username, fetched_stories.id)
