from dataclasses import dataclass, field
from datetime import date
from typing import Collection, Iterable, Literal, Optional, Union

from ...models import cached, mixins
from ...models.diff import Diff, UserDiff
from ..constants import (
    CHANGES_ATTRS,
    DATE_OUTPUT_FORMAT,
    ChangesType,
    DiffsType,
    ListsType,
)
from ..streams import ColoredOutput

USER_COMPARISON_TEXT_TABLE = {
    "mutuals": "mutuals",
    "diff": "differences",
    "both": "mutuals and differences",
}


@dataclass
class DiffRenderer:
    out: ColoredOutput
    lists: Iterable[ListsType]
    changes: Iterable[ChangesType]
    username: Optional[str]
    detailed: bool

    def render(self, user_update: Union[mixins.UserUpdate, UserDiff]) -> None:
        """Renders updates that were performed in a user list between two points in time
        (e.g. added/removed/renamed users)

        Args:
            user_update (BasicUserUpdate): The updates that were performed
        """
        block_renderer = (
            self.render_block_with_username_filter
            if self.username is not None
            else self.render_block
        )
        for list_name in self.lists:
            block_renderer(list_name, getattr(user_update, list_name))

    def render_block(
        self, list_name: ListsType, update: Union[mixins.Update, Diff]
    ) -> None:
        if list_name not in self.lists:
            return
        if not update:
            self.out.write(f"{list_name.capitalize()}: No Update\n")
            return
        self.out.write(f"{list_name.capitalize()}:\n")

        for change_type in self.changes:
            usernames: frozenset[str] = getattr(update, f"{change_type}_usernames")
            if not usernames:
                continue
            self.render_change_header(change_type, usernames)

            if not self.detailed:
                continue
            self.render_username_list(change_type, usernames)

    def render_block_with_username_filter(
        self, list_name: ListsType, update: Union[mixins.Update, Diff]
    ):
        if list_name not in self.lists:
            return
        if update.is_empty(self.username):
            return

        self.out.write(f"{list_name.capitalize()}:\n")
        for change_type in self.changes:
            if not getattr(update, f"has_username_on_{change_type}")(self.username):
                continue
            self.render_username(change_type)

    def render_change_header(
        self,
        change_type: ChangesType,
        userset: Collection[str],
    ):
        sign, color = CHANGES_ATTRS[change_type]
        self.out.color = color
        self.out.attrs = ("bold",)
        self.out.write("  ")
        self.out.cwrite(f"{sign.strip()}{len(userset)} {change_type}")
        self.out.write("\n")
        self.out.attrs = ("bold", "underline")

    def render_username(self, change_type: ChangesType):
        sign, color = CHANGES_ATTRS[change_type]
        self.out.color = color
        self.out.write("  ")
        self.out.cwrite(f"{sign}{self.username}")
        self.out.write("\n")

    def render_username_list(
        self,
        change_type: ChangesType,
        userset: Collection[str],
    ):
        sign, color = CHANGES_ATTRS[change_type]
        self.out.color = color
        for username in userset:
            self.out.write("    ")
            self.out.cwrite(f"{sign}{username}")
            self.out.write("\n")


@dataclass
class RecordsDiffRenderer(DiffRenderer):
    from_date: Optional[date]
    to_date: Optional[date]

    def render(self, user_update: mixins.UserUpdate) -> None:  # type: ignore[override]
        self.render_header()
        super().render(user_update)

    def render_header(self) -> None:
        self.out.write("Account Update\n")
        if self.from_date is not None:
            self.out.write(f"From: {self.from_date.strftime('%A %d %B %Y')}\n")
        if self.to_date is not None:
            self.out.write(f"To: {self.to_date.strftime('%A %d %B %Y')}\n")
        self.out.write("\n")


@dataclass
class ChangelogRenderer(DiffRenderer):
    target: str
    changelog: Iterable[cached.ChangelogEntry]
    all: bool

    def render(self) -> None:  # type: ignore[override]
        """Renders the full list of log entries (from most recent to the oldest one),
        each including updates such as added/removed/renamed users"""
        extra_header = (
            f"Filtered by username: {self.username}\n"
            if self.username is not None
            else ""
        )
        self.out.write(f"Logs for {self.target}\n{extra_header}\n")

        for log in self.changelog:
            empty_log: bool = log.is_empty(self.username)
            if not self.all and empty_log:
                continue
            self.render_log_header(log)
            if empty_log and self.username is not None:
                self.out.write("No Update\n\n")
                continue
            super().render(log)
            self.out.write("\n")

    def render_log_header(self, log: cached.ChangelogEntry) -> None:
        self.out.write(f"Changelog - {log.timestamp.strftime(DATE_OUTPUT_FORMAT)}\n")


@dataclass(frozen=True)
class UsersDiffRendererData:
    name: str
    date: Optional[date]
    data: mixins.User

    def __str__(self) -> str:
        return (
            f"'{self.name}' ({self.date.strftime('%d/%m/%Y')})"
            if self.date is not None
            else f"'{self.name}'"
        )


@dataclass
class UsersDiffRenderer(DiffRenderer):
    changes: Iterable[DiffsType] = field(init=False)  # type: ignore[override]
    username: Optional[str] = field(init=False)
    diff_attrs: dict[DiffsType, str] = field(init=False)  # type: ignore[override]
    user1: UsersDiffRendererData
    user2: UsersDiffRendererData
    comparison_type: Literal["mutuals", "diff", "both"]

    def __post_init__(self):
        self.username = None
        if self.comparison_type == "mutuals":
            self.changes = ("mutuals",)
        elif self.comparison_type == "diff":
            self.changes = ("user1", "user2")
        else:
            self.changes = ("mutuals", "user1", "user2")  # type: ignore[override]
        self.diff_attrs = {
            "user1": self.user1.name,
            "user2": self.user2.name,
            "mutuals": "mutuals",
        }

    def render(self):  # type: ignore[override]
        self.out.write(
            f"User Comparison ({USER_COMPARISON_TEXT_TABLE[self.comparison_type]})\n"
        )
        self.out.write(f"Between: {self.user1} and {self.user2}\n")
        super().render(
            self.user1.data.diffs_from(self.user2.data, self.lists, self.changes)
        )

    def render_change_header(  # type: ignore[override]
        self, change_type: DiffsType, userset: Collection[str]
    ):
        self.out.attrs = ("bold",)
        self.out.color = "light_cyan"
        self.out.write("  ")
        self.out.cwrite(f"{self.diff_attrs[change_type]} ({len(userset)})")
        self.out.write("\n")
        self.out.attrs = ("bold", "underline")

    def render_username_list(  # type: ignore[override]
        self, change_type: DiffsType, userset: Collection[str]
    ):
        self.out.color = "green"
        for username in userset:
            self.out.write("    ")
            self.out.cwrite(username)
            self.out.write("\n")
