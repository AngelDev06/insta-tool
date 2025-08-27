from dataclasses import dataclass
from datetime import date
from itertools import tee
from typing import Iterable, Optional

from ...models import cached
from ...models.viewer import Viewer
from ..constants import DATE_OUTPUT_FORMAT
from ..streams import ColoredOutput


@dataclass
class ViewerHistoryRenderer:
    out: ColoredOutput
    username: str
    from_date: Optional[date]
    to_date: Optional[date]
    all: bool
    deep: bool

    def render(self, stories: Iterable[cached.Story]):
        lookup_success: bool = False
        self.out.set_attrs(color="green", attrs=("bold", "underline"))
        self.render_header()

        if self.deep:
            stories, itr = tee(stories)
            uid = self.lookup_uid(itr)
            if uid is None:
                self.render_failed_result()
                return

            def lookup(story: cached.Story) -> Optional[Viewer]:
                return story.viewers.get(uid)

        else:

            def lookup(story: cached.Story) -> Optional[Viewer]:
                for viewer in story.viewers.values():
                    if viewer.name == self.username:
                        return viewer
                return None

        for story in stories:
            viewer = lookup(story)
            if viewer is not None or self.all:
                self.render_entry(story, viewer)
                lookup_success = True

        if not lookup_success:
            self.render_failed_result()

    def render_failed_result(self):
        self.out.set_attrs(color="red")
        self.out.cwrite(
            "Viewer lookup failed, no records of the specified user were found"
        )
        self.out.write("\n")

    def render_entry(self, story: cached.Story, viewer: Optional[Viewer]) -> None:
        self.out.write(f"Story - {story.timestamp.strftime(DATE_OUTPUT_FORMAT)}\n")
        if viewer is None:
            self.out.set_attrs(color="red")
            self.out.cwrite("No Records")
            self.out.set_attrs(color="green")
            self.out.write("\n\n")
            return
        self.out.cwrite(
            f"Viewer recorded at: {viewer.recorded_at.strftime(DATE_OUTPUT_FORMAT)}"
        )
        self.out.write("\n\n")

    def render_header(self) -> None:
        self.out.write("Story Viewer History Lookup\n")
        self.out.write(f"Target: {self.username}\n")
        date_txt: list[str] = []
        if self.from_date is not None:
            date_txt.append(f"From: {self.from_date.strftime('%d/%m/%Y')}")
        if self.to_date is not None:
            date_txt.append(f"Up To: {self.to_date.strftime('%d/%m/%Y')}")
        if date_txt:
            self.out.write(f"{', '.join(date_txt)}\n")
        self.out.write("\n")

    def lookup_uid(self, stories: Iterable[cached.Story]) -> Optional[int]:
        for story in stories:
            for uid, viewer in story.viewers.items():
                if viewer.name == self.username:
                    return uid
        return None
