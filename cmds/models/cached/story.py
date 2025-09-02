from datetime import datetime, date
from typing import ClassVar, Union, Optional

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
                    timestamp=story.timestamp, viewers=story.viewers
                )

        self.dump(fetched_stories.username, fetched_stories.id)

    def at(self, sid_or_date: Union[int, date]) -> tuple[int, Optional[Story]]:
        if isinstance(sid_or_date, int):
            return sid_or_date, self.stories.get(sid_or_date)
        if not isinstance(sid_or_date, date):
            raise TypeError(
                "`sid_or_date` should be a valid date or a story id"
            )
        
        for sid, story in self.stories.items():
            if story.timestamp.date() == sid_or_date:
                return sid, story
        return 0, None
