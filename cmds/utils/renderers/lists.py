from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

from ...models import mixins
from ..constants import ListsType
from ..streams import ColoredOutput


@dataclass
class BasicListRenderer:
    out: ColoredOutput

    def render(self, userset: frozenset[str]):
        for username in userset:
            self.out.write("  ")
            self.out.cwrite(username)
            self.out.write("\n")


@dataclass
class ListsDiffRenderer(BasicListRenderer):
    at: Optional[date]
    reverse: bool

    def render(self, userset: frozenset[str]):
        comparison_txt = (
            "followings - followers" if not self.reverse else "followers - followings"
        )
        date_txt = f" - {self.at.strftime('%d/%m/%Y')}" if self.at is not None else ":"
        self.out.write(f"Diff ({comparison_txt}){date_txt}\n")
        super().render(userset)


@dataclass
class HistoryPointRenderer(BasicListRenderer):
    history_point: date
    lists: Iterable[ListsType]
    state: mixins.User
    target: str
    username: Optional[str]
    summary: bool

    def render(self):  # type: ignore[override]
        history_point_txt = self.history_point.strftime("%d/%m/%Y")
        self.out.write(f"History for {self.target} at {history_point_txt}\n")
        additional_text: list[str] = []

        for list_name in self.lists:
            userset: frozenset[str] = getattr(self.state, f"{list_name}_usernames")
            if self.username is not None:
                if self.username in userset:
                    additional_text.append(f"a {list_name[:-1]}")
                continue
            if self.summary:
                self.out.write(f"{list_name.capitalize()}: {len(userset)}\n")
                continue
            self.out.write(f"{list_name.capitalize()} ({len(userset)}):\n")
            super().render(userset)

        if self.username is not None:
            if not additional_text:
                self.out.write(
                    f"{self.username} was neither a follower nor a following\n"
                )
                return
            self.out.write(
                f"{self.username} was {' and '.join(additional_text)} of {self.target}\n"
            )
