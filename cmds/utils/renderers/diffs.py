from dataclasses import dataclass, field
from datetime import date
from typing import Collection, Literal, Optional, TypeAlias

from ...models import cached, mixins
from ...models.diff import SingleDiff
from ...models.update import SingleUpdate, Update, UserUpdate
from ..constants import (
    CHANGES_ATTRS,
    DATE_OUTPUT_FORMAT,
    ChangesType,
    DiffsType,
    ListsType,
)
from ..filters import date_filter
from ..streams import ColoredOutput

USER_COMPARISON_TEXT_TABLE = {
    "mutuals": "mutuals",
    "diff": "differences",
    "both": "mutuals and differences",
}
UserComparisonType: TypeAlias = Literal["mutuals", "diff", "both"]


@dataclass
class DiffRenderer:
    out: ColoredOutput
    lists: Collection[ListsType]
    changes: Collection[ChangesType]
    username: Optional[str]
    detailed: bool

    def render(self, user_update: UserUpdate) -> None:
        """Renders updates that were performed (either involving a specific user or the whole list)

        Args:
            user_update (UserUpdate): The updates that were performed
        """
        # for specific user updates we just render their name
        # for the whole lists we also render a change header along with usernames
        block_renderer = (
            self.render_username
            if self.username is not None
            else self.render_block
        )
        for list_name in self.lists:
            update = getattr(user_update, list_name)
            if not update:
                continue
            self.out.write(f"{list_name.capitalize()}:\n")
            block_renderer(update)

    def render_header(self):
        self.out.write("Filters:\n")
        if self.username is not None:
            self.out.write(f"  Username: {self.username}\n")
        self.out.write(f"  Lists: {', '.join(self.lists)}\n")
        self.out.write(f"  Changes: {', '.join(self.changes)}\n")
        self.out.write(f"  Detailed: {self.detailed}\n")

    def render_block(self, update: Update) -> None:
        for change_type in self.changes:
            change: dict[int, str] = getattr(update, change_type)
            if not change:
                continue
            usernames: list[str] = list(change.values())
            self.render_change_header(change_type, usernames)

            if not self.detailed:
                continue
            self.render_username_list(change_type, usernames)

    def render_change_header(
        self,
        change_type: ChangesType,
        userset: Collection[str],
    ):
        sign, color = CHANGES_ATTRS[change_type]
        self.out.set_attrs(color=color, attrs=("bold",))
        self.out.write("  ")
        self.out.cwrite(f"{sign.strip()}{len(userset)} {change_type}")
        self.out.write("\n")
        self.out.set_attrs(attrs=("bold", "underline"))

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

    def render_username(self, update: SingleUpdate):
        sign, color = CHANGES_ATTRS[update.change]
        self.out.set_attrs(color=color)
        self.out.write("  ")
        self.out.cwrite(f"{sign}{update.username}")
        self.out.write("\n")


@dataclass
class RecordsDiffRenderer(DiffRenderer):
    from_date: Optional[date]
    to_date: Optional[date]

    def render(self, user_update: UserUpdate) -> None:
        self.render_header()
        super().render(user_update)

    def render_header(self) -> None:
        self.out.write("Account Update\n")
        super().render_header()
        if self.from_date is not None:
            self.out.write(f"From: {self.from_date.strftime('%A %d %B %Y')}\n")
        if self.to_date is not None:
            self.out.write(f"To: {self.to_date.strftime('%A %d %B %Y')}\n")
        self.out.write("\n")


@dataclass
class ChangelogRenderer(DiffRenderer):
    target: str
    from_date: Optional[date]
    to_date: Optional[date]
    all: bool

    def render(self, changelog: list[cached.ChangelogEntry]) -> None:  # type: ignore[override]
        """Renders the full list of log entries (from most recent to the oldest one),
        each including updates such as added/removed/renamed users"""
        self.render_header()

        for log in date_filter(
            self.from_date, self.to_date, reversed(changelog)
        ):
            updates = log.pack_updates(self.username, self.lists, self.changes)
            if not updates:
                if self.all:
                    self.render_log_header(log)
                    self.out.write("No Update\n\n")
                continue

            self.render_log_header(log)
            if self.username is not None and not updates:
                self.out.write("No Update\n\n")
                continue
            super().render(updates)
            self.out.write("\n")

    def render_log_header(self, log: cached.ChangelogEntry) -> None:
        self.out.write(
            f"Changelog - {log.timestamp.strftime(DATE_OUTPUT_FORMAT)}\n"
        )

    def render_header(self) -> None:
        self.out.write(f"Logs for {self.target}\n")
        super().render_header()
        if self.from_date is not None:
            self.out.write(
                f"  From Date: {self.from_date.strftime('%d/%m/%Y')}\n"
            )
        if self.to_date is not None:
            self.out.write(f"  To Date: {self.to_date.strftime('%d/%m/%Y')}\n")
        self.out.write(f"  Include All: {self.all}\n")
        self.out.write("\n")


@dataclass(frozen=True)
class UsersDiffRendererData:
    name: str
    date: Optional[date]
    info: mixins.User

    def __str__(self) -> str:
        return (
            f"'{self.name}' ({self.date.strftime('%d/%m/%Y')})"
            if self.date is not None
            else f"'{self.name}'"
        )


@dataclass
class UsersDiffRenderer(DiffRenderer):
    changes: Collection[DiffsType] = field(init=False)  # type: ignore[override]
    diff_attrs: dict[DiffsType, str] = field(init=False)  # type: ignore[override]
    comparison_type: UserComparisonType

    def __post_init__(self):
        if self.comparison_type == "mutuals":
            self.changes = ("mutuals",)
        elif self.comparison_type == "diff":
            self.changes = ("user1", "user2")
        else:
            self.changes = ("mutuals", "user1", "user2")  # type: ignore[override]

    def render(  # type: ignore[override]
        self, user1: UsersDiffRendererData, user2: UsersDiffRendererData
    ):
        self.diff_attrs = {
            "user1": user1.name,
            "user2": user2.name,
            "mutuals": "mutuals",
        }
        self.out.write(
            f"User Comparison ({USER_COMPARISON_TEXT_TABLE[self.comparison_type]})\n"
        )
        self.out.write(f"Between: {user1} and {user2}\n")
        super().render(
            user1.info.diffs_from(
                user2.info, self.username, self.lists, self.changes
            )
        )

    def render_change_header(  # type: ignore[override]
        self, change_type: DiffsType, userset: Collection[str]
    ):
        self.out.set_attrs(color="light_cyan", attrs=("bold",))
        self.out.write("  ")
        self.out.cwrite(f"{self.diff_attrs[change_type]} ({len(userset)})")
        self.out.write("\n")
        self.out.set_attrs(attrs=("bold", "underline"))

    def render_username_list(  # type: ignore[override]
        self, change_type: DiffsType, userset: Collection[str]
    ):
        self.out.color = "green"
        for username in userset:
            self.out.write("    ")
            self.out.cwrite(username)
            self.out.write("\n")

    def render_username(self, update: SingleDiff):  # type: ignore[override]
        self.out.set_attrs(color="green")
        self.out.write("    ")
        self.out.cwrite(str(update.username))
        self.out.write("\n")

@dataclass
class ViewersDiffRenderer(DiffRenderer):
    lists: Collection[Literal["viewers"]] = field(init=False)
    
    def __post_init__(self):
        self.lists = ("viewers",) # type: ignore[override]
    
    def render(self, story1: mixins.Story, story2: mixins.Story): # type: ignore[override]
        self.render_header(story1, story2)
        
        update = story2.updates_from(story1, self.username, self.changes)
        if not update:
            self.out.write("No Update\n")
            return
        if self.username is None:
            super().render_block(update)
        else:
            super().render_username(update)
    
    def render_header(self, story1: mixins.Story, story2: mixins.Story): # type: ignore[override]
        self.out.write("Story Viewers Update\n")
        self.out.write(f"From Story at Date: {story1.timestamp.strftime(DATE_OUTPUT_FORMAT)}\n")
        self.out.write(f"To Story at Date: {story2.timestamp.strftime(DATE_OUTPUT_FORMAT)}\n")
        self.out.write("Filters:\n")
        if self.username is not None:
            self.out.write(f"  Username: {self.username}\n")
        self.out.write(f"  Changes: {', '.join(self.changes)}\n")
        self.out.write(f"  Detailed: {self.detailed}\n\n")
