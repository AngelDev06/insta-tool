from dataclasses import dataclass
from datetime import date, datetime
from itertools import product
from typing import (
    Iterable,
    Optional,
    Unpack,
    TypeAlias,
    Union,
    Literal,
    cast,
    TypedDict,
    NotRequired,
)
from .streams import ColoredOutput
from .cache import UserLists, OutputUpdateKwargsType, ChangelogCacheType

ChangesInfoType: TypeAlias = Iterable[
    Union[
        tuple[Literal["added"], Literal["+"], Literal["green"]],
        tuple[Literal["removed"], Literal["-"], Literal["red"]],
    ]
]
ListsType: TypeAlias = Literal["followers", "followings"]
ChangesType: TypeAlias = Literal["added", "removed"]
IsEmptyLogType: TypeAlias = dict[
    Literal["followers", "followings"],
    dict[Literal["added", "removed"], bool],
]

DATE_OUTPUT_FORMAT = "%d/%m/%Y %I:%M:%S%p"
CHANGES_TABLE = {
    "added": ("added", "+", "green"),
    "removed": ("removed", "-", "red"),
}


class RenderKwargsType(TypedDict):
    added: NotRequired[UserLists]
    removed: NotRequired[UserLists]


@dataclass
class BasicListRenderer:
    out: ColoredOutput

    def render(self, userset: set[str]):
        for username in userset:
            self.out.write("  ")
            self.out.cwrite(username)
            self.out.write("\n")


@dataclass
class ListsDiffRenderer(BasicListRenderer):
    at: Optional[date]
    reverse: bool

    def render(self, userset: set[str]):
        comparison_txt = (
            "followings - followers"
            if not self.reverse
            else "followers - followings"
        )
        date_txt = (
            f" - {self.at.strftime('%d/%m/%Y')}"
            if self.at is not None
            else ":"
        )
        self.out.write(f"Diff ({comparison_txt}){date_txt}\n")
        super().render(userset)


@dataclass
class HistoryPointRenderer(BasicListRenderer):
    history_point: date
    lists: Iterable[ListsType]
    user_lists: UserLists
    target: str
    username: Optional[str]
    summary: bool

    def render(self):  # type: ignore[override]
        history_point_txt = self.history_point.strftime("%d/%m/%Y")
        self.out.write(f"History for {self.target} at {history_point_txt}\n")
        additional_text: list[str] = []

        for list_name in self.lists:
            userset: set[str] = getattr(self.user_lists, list_name)
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


@dataclass
class DiffRenderer:
    out: ColoredOutput
    lists: Iterable[ListsType]
    changes: Iterable[ChangesType]
    username: Optional[str]
    detailed: bool

    def render(self, **kwargs: Unpack[RenderKwargsType]) -> None:
        block_renderer = (
            self.render_block_with_username_filter
            if self.username is not None
            else self.render_block
        )
        for list_name in self.lists:
            block_renderer(
                list_name,
                **{
                    change_type: getattr(userset, list_name)
                    for change_type, userset in kwargs.items()
                },
            )

    def render_block(
        self,
        list_name: ListsType,
        **kwargs: Unpack[OutputUpdateKwargsType],
    ) -> None:
        if list_name not in self.lists:
            return
        if not any(userset for userset in kwargs.values()):
            self.out.write(f"{list_name.capitalize()}: No Update\n")
            return
        self.out.write(f"{list_name.capitalize()}:\n")

        for change_type, sign, color in self.changes_attrs:
            userset = kwargs[change_type]  # type: ignore
            if not userset:
                continue
            self.out.write("  ")
            self.out.color = color
            self.out.attrs = ("bold",)
            self.out.cwrite(f"{sign}{len(userset)} {change_type}")
            self.out.write("\n")
            self.out.attrs = ("bold", "underline")

            if not self.detailed:
                continue

            for username in userset:
                self.out.write("    ")
                self.out.cwrite(f"{sign} {username}")
                self.out.write("\n")

    def render_block_with_username_filter(
        self, list_name: ListsType, **kwargs: Unpack[OutputUpdateKwargsType]
    ):
        entries_status = {
            change_type: self.username in userset  # type: ignore
            for change_type, userset in kwargs.items()
        }
        if not any(
            entries_status[change_type] for change_type in self.changes
        ):
            return

        self.out.write(f"{list_name.capitalize()}:\n")
        for change_type, sign, color in self.changes_attrs:
            if not entries_status[change_type]:
                continue
            self.out.color = color
            self.out.write("  ")
            self.out.cwrite(f"{sign} {self.username}")
            self.out.write("\n")

    @property
    def changes_attrs(self) -> ChangesInfoType:
        return cast(
            ChangesInfoType,
            (CHANGES_TABLE[change_type] for change_type in self.changes),
        )


@dataclass
class RecordsDiffRenderer(DiffRenderer):
    from_date: Optional[date]
    to_date: Optional[date]

    def render(self, **kwargs: Unpack[RenderKwargsType]) -> None:
        self.render_header()
        super().render(**kwargs)

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
    changelog: Iterable[ChangelogCacheType]
    all: bool

    def render(self) -> None:  # type: ignore[override]
        extra_header = (
            f"Filtered by username: {self.username}\n"
            if self.username is not None
            else ""
        )
        self.out.write(f"Logs for {self.target}\n{extra_header}\n")

        log_is_empty_checker = (
            self.is_empty_for_username
            if self.username is not None
            else self.is_empty
        )
        for log in self.changelog:
            empty_log: bool = log_is_empty_checker(log)
            if not self.all and empty_log:
                continue
            self.render_log_header(log)
            if empty_log and self.username is not None:
                self.out.write("No Update\n\n")
                continue
            # render changes per list
            super().render(
                **{
                    change_type: UserLists(
                        **{
                            list_name: set(log[list_name][change_type])
                            for list_name in self.lists
                        }
                    )
                    for change_type in self.changes
                }
            )
            self.out.write("\n")

    def render_log_header(self, log: ChangelogCacheType) -> None:
        date = datetime.fromtimestamp(log["timestamp"]).strftime(
            DATE_OUTPUT_FORMAT
        )
        self.out.write(f"Changelog - {date}\n")

    def is_empty(self, log: ChangelogCacheType) -> bool:
        return not any(
            log[list_name][change_type]
            for list_name, change_type in product(self.lists, self.changes)
        )

    def is_empty_for_username(self, log: ChangelogCacheType) -> bool:
        return not any(
            self.username in log[list_name][change_type]
            for list_name, change_type in product(self.lists, self.changes)
        )
