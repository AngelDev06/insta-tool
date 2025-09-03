from datetime import datetime, date
from typing import ClassVar, Union, Optional, Iterable, Callable
from itertools import takewhile, dropwhile

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

        if fetched_stories:
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

    @staticmethod
    def _range_not_started(
        start: Optional[Union[int, date]],
    ) -> Callable[[tuple[int, Story]], bool]:
        if start is None:
            return lambda _: False
        if isinstance(start, int):
            return lambda item: item[0] != start
        if isinstance(start, date):
            return lambda item: item[1].timestamp.date() < start
        raise TypeError("`start` is expected to be a valid date or story id")

    @staticmethod
    def _range_should_continue(
        end: Optional[Union[int, date]],
    ) -> Callable[[tuple[int, Story]], bool]:
        if end is None:
            return lambda _: True
        if isinstance(end, int):
            return lambda item: item[0] != end
        if isinstance(end, date):
            return lambda item: item[1].timestamp.date() <= end
        raise TypeError("`end` is expected to be a valid date or story id")

    def range(
        self,
        start: Optional[Union[int, date]],
        end: Optional[Union[int, date]],
    ) -> Iterable[tuple[int, Story]]:
        return takewhile(
            self._range_should_continue(end),
            dropwhile(self._range_not_started(start), self.stories.items()),
        )
