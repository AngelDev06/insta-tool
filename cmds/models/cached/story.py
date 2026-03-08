from datetime import date, datetime
from itertools import dropwhile, takewhile
from typing import Any, Callable, ClassVar, Iterable, Iterator, Optional, Union

from pydantic import BaseModel, Field, field_serializer, field_validator

from ...utils.constants import DATE_OUTPUT_FORMAT
from ...utils.tool_logger import logger
from ...utils.uids import UIDMap
from .. import fetched, mixins
from ..viewer import Viewer


class Story(mixins.Story, BaseModel):
    timestamp: datetime
    viewers: dict[int, Viewer]

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime, _info):
        return timestamp.timestamp()

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, timestamp: Any) -> datetime:
        if isinstance(timestamp, str):
            return datetime.strptime(timestamp, DATE_OUTPUT_FORMAT)
        if isinstance(timestamp, float):
            return datetime.fromtimestamp(timestamp)
        raise TypeError("invalid type of timestamp")


class StoryHistory(mixins.Cached, BaseModel):
    subdir: ClassVar[str] = "stories"
    stories: dict[int, Story] = Field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.stories)

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

    def at(
        self, sid_or_date: Union[int, date], select_last: bool = False
    ) -> tuple[int, Optional[Story]]:
        if isinstance(sid_or_date, int):
            return sid_or_date, self.stories.get(sid_or_date)
        if not isinstance(sid_or_date, date):
            raise TypeError("`sid_or_date` should be a valid date or a story id")

        result: tuple[int, Optional[Story]] = (0, None)

        for sid, story in self.stories.items():
            if story.timestamp.date() == sid_or_date:
                result = (sid, story)
                if not select_last:
                    break
                continue
            if select_last and result[0]:
                break

        return result

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

    def lookup(
        self,
        username: str,
        from_point: Optional[Union[int, date]] = None,
        to_point: Optional[Union[int, date]] = None,
        deep: bool = False,
        all: bool = False,
    ) -> Iterable[tuple[int, Story, Optional[Viewer]]]:
        if deep:
            uid = self.lookup_uid(username)
            if uid is None:
                return []

            def find(story: Story) -> Optional[Viewer]:
                return story.viewers.get(uid)

        else:

            def find(story: Story) -> Optional[Viewer]:
                for viewer in story.viewers.values():
                    if viewer.name == username:
                        return viewer
                return None

        def search() -> Iterator[tuple[int, Story, Optional[Viewer]]]:
            for sid, story in self.range(from_point, to_point):
                viewer = find(story)
                if viewer is not None:
                    yield sid, story, viewer
                elif all:
                    yield sid, story, None

        return search()

    def lookup_uid(self, username: str) -> Optional[int]:
        for story in self.stories.values():
            for uid, viewer in story.viewers.items():
                if viewer.name == username:
                    return uid
        return None

    def delete(self, owner: str, record: Union[date, int]) -> bool:
        if not self.stories:
            return False
        if isinstance(record, int):
            return bool(self.stories.pop(record, None))

        captured: Optional[tuple[int, Story]] = None
        iterator = reversed(self.stories.items())

        for sid, story in iterator:
            if story.timestamp.date() != record:
                if not captured:
                    continue
                break

            if not captured:
                captured = (sid, story)
                continue

            options = list(
                takewhile(lambda item: item[1].timestamp.date() == record, iterator)
            )  # newest to oldest
            options[0:0] = [captured, (sid, story)]

            print("Multiple stories were found on specified date:")
            for index, (sid2, story2) in enumerate(options, 1):
                print(
                    f"{index}: Story ({sid2}, {story2.timestamp.strftime(DATE_OUTPUT_FORMAT)})"
                )

            selection = input("Specify which one to remove by index: ").strip()
            if not selection.isdigit():
                return False
            selection = int(selection)
            if not selection or selection > len(options):
                return False

            captured = options[selection - 1]
            break

        if not captured:
            return False

        self.stories.pop(captured[0])
        uid = UIDMap.get().uid_of(owner)
        if uid is None:
            logger.critical(f"User ID of story owner {owner} not registered")
            raise RuntimeError("Missing UID")
        self.dump(owner, uid)
        return True
