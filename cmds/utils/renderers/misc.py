from dataclasses import dataclass
from datetime import date
from typing import Optional

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

    def render(self, items: list[tuple[int, cached.Story, Optional[Viewer]]]):
        self.out.set_attrs(color="green", attrs=("bold", "underline"))
        self.render_header()

        if not items:
            self.out.set_attrs(color="red")
            self.out.cwrite(
                "Viewer lookup failed, no records of the specified user were found"
            )
            self.out.write("\n")
            return

        for sid, story, viewer in reversed(items):
            self.render_entry(sid, story, viewer)

    def render_entry(
        self, sid: int, story: cached.Story, viewer: Optional[Viewer]
    ) -> None:
        self.out.write(
            f"Story ({sid}) - {story.timestamp.strftime(DATE_OUTPUT_FORMAT)}\n"
        )
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
