from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from ...utils.constants import DATE_OUTPUT_FORMAT
from ...utils.scrapping import Scrapper
from ...utils.tool_logger import logger
from .. import mixins
from ..viewer import Viewer

if TYPE_CHECKING:
    from instagrapi import Client
    from instagrapi.types import Story as InstaStory


@dataclass
class Story(mixins.Story):
    """A single story entry (fetched online and ready to be cached). Unlike with state, multiple story entries can exist at a single point in time so a container of this instance is required"""

    taken_at: datetime
    viewers: dict[int, Viewer]

    @classmethod
    def fetch(cls, story: InstaStory, client: Client, chunk_size: int):
        scrapper = Scrapper(client=client, target_id=story.pk, chunk_size=chunk_size)
        logger.info(
            f"fetching viewers from story at: {story.taken_at.strftime(DATE_OUTPUT_FORMAT)}"
        )
        viewers: dict[int, str] = scrapper.fetch_story_viewers()
        logger.info(f"fetched viewers, total count: {len(viewers)}")
        return cls(
            taken_at=story.taken_at,
            viewers={
                key: Viewer.model_construct(name=value, recorded_at=datetime.now())
                for key, value in viewers.items()
            },
        )


@dataclass
class Stories:
    username: str
    id: int
    stories: dict[int, Story] = field(default_factory=dict)

    @classmethod
    def fetch(cls, client: Client, target_username: str, chunk_size: int = 100):
        logger.info(f"fetching user id and stories info of: {target_username}")
        uid: str = client.user_id_from_username(target_username)
        stories = client.user_stories(uid)

        if not stories:
            logger.info("no stories currently available")
            return cls(username=target_username, id=int(uid))

        logger.info("fetched stories info, proceeding with fetching viewers...")

        return cls(
            username=target_username,
            id=int(uid),
            stories={
                int(story.pk): Story.fetch(story, client, chunk_size)
                for story in stories
            },
        )

    def __iter__(self):
        return iter(self.stories.items())
