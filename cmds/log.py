from argparse import ArgumentParser, FileType, Namespace, ArgumentTypeError
from sys import stdout
from typing import cast, TextIO, Iterable, Union, Literal, Optional, TypedDict
from datetime import datetime, date
from termcolor import colored
from itertools import product
from .utils.login import get_credentials, login
from .utils.cache import Cache, UserCache, ChangelogCacheType
from .utils.user_info import UserInfo

DATE_OUTPUT_FORMAT = "%d/%m/%Y %I:%M:%S%p"
ENTRIES_PAIRS: tuple[
    tuple[Literal["followers"], Literal["followings"]],
    tuple[Literal["added"], Literal["removed"]],
] = (("followers", "followings"), ("added", "removed"))


class EntriesStatusSubtype(TypedDict):
    added: bool
    removed: bool


class EntriesStatusType(TypedDict):
    followers: EntriesStatusSubtype
    followings: EntriesStatusSubtype


def _date_parser(argument: str) -> date:
    try:
        return datetime.strptime(argument, "%d-%m-%Y").date()
    except ValueError:
        raise ArgumentTypeError(f"'{argument}' is not a proper date")


def _date_filter(
    args: Namespace, changelog: Iterable[ChangelogCacheType]
) -> Iterable[ChangelogCacheType]:
    if args.from_date is not None and args.to_date is not None:

        def filterer(item: ChangelogCacheType) -> bool:
            log_date = date.fromtimestamp(item["timestamp"])
            return args.from_date <= log_date <= args.to_date

        return filter(filterer, changelog)
    if args.from_date is not None:
        return (
            item
            for item in changelog
            if date.fromtimestamp(item["timestamp"]) >= args.from_date
        )
    if args.to_date is not None:
        return (
            item
            for item in changelog
            if date.fromtimestamp(item["timestamp"]) <= args.to_date
        )
    return changelog


def _list_filter(args: Namespace) -> Union[tuple[str], tuple[str, str]]:
    if args.list is None:
        return ("followers", "followings")
    if args.list == "followers":
        return ("followers",)
    return ("followings",)


def _change_filter(args: Namespace) -> Iterable[tuple[str, str, str]]:
    ADDED = ("added", "+", "green")
    REMOVED = ("removed", "-", "red")
    if args.change is None:
        return (ADDED, REMOVED)
    if args.change == "added":
        return (ADDED,)
    return (REMOVED,)


class Renderer:
    def __init__(self, args: Namespace, cache: UserCache) -> None:
        self.out: TextIO = args.out
        self.lists = _list_filter(args)
        self.changes = _change_filter(args)
        self.target: str = args.target
        self.username: Optional[str] = args.username
        self.changelog: Iterable[ChangelogCacheType] = _date_filter(
            args, reversed(cache.changelog)
        )
        self.all: bool = args.all
        self.detailed: bool = args.detailed

    def style(
        self,
        text: str,
        color: str,
        attrs: Iterable[str] = ("bold", "underline"),
    ) -> str:
        return (
            colored(text, color, attrs=attrs) if self.out is stdout else text
        )

    def render(self) -> None:
        # header rendering
        extra_header = (
            f"Filtered by username: {self.username}\n"
            if self.username is not None
            else ""
        )
        self.out.write(f"Logs for {self.target}\n{extra_header}\n")

        log_renderer = (
            self._render_log_block_default
            if self.username is None
            else self._render_log_block_with_username_filter
        )
        for log in self.changelog:
            log_renderer(log)

    def _render_log_block_default(self, log: ChangelogCacheType) -> None:
        if not self.all and self._empty_log(log):
            return
        self._render_log_header(log)

        for list_name in self.lists:
            self.out.write(f"{list_name.capitalize()}:\n")

            for change_type, sign, color in self.changes:
                self.out.write("  ")
                self.out.write(
                    self.style(
                        f"{sign}{len(log[list_name][change_type])} {change_type}",
                        color,
                        attrs=("bold",),
                    )
                )
                self.out.write("\n")

                if not self.detailed:
                    continue

                for username in log[list_name][change_type]:
                    self.out.write("    ")
                    self.out.write(self.style(f"{sign} {username}", color))
                    self.out.write("\n")

        self.out.write("\n")

    def _render_log_block_with_username_filter(
        self, log: ChangelogCacheType
    ) -> None:
        entries_status: EntriesStatusType = {  # type: ignore
            list_name: {
                change_type: self.username in log[list_name][change_type]
                for change_type in ENTRIES_PAIRS[1]
            }
            for list_name in ENTRIES_PAIRS[0]
        }
        empty_log: bool = self._empty_log(entries_status)

        if empty_log and not self.all:
            return
        self._render_log_header(log)
        if empty_log:
            self.out.write("No Update\n\n")
            return

        for list_name in self.lists:
            if (
                not entries_status[list_name]["added"]
                and not entries_status[list_name]["removed"]
            ):
                continue

            self.out.write(f"{list_name.capitalize()}:\n")
            for change_type, sign, color in self.changes:
                if not entries_status[list_name][change_type]:
                    continue
                self.out.write("  ")
                self.out.write(self.style(f"{sign} {self.username}", color))
                self.out.write("\n")

        self.out.write("\n")

    # Note: this works for `entries_status` defined in `_render_log_block_with_username_filter` as well
    def _empty_log(
        self, log: Union[ChangelogCacheType, EntriesStatusType]
    ) -> bool:
        return not any(
            (
                log[list_name][change_type]
                for list_name, change_type in product(*ENTRIES_PAIRS)
            )
        )

    def _render_log_header(self, log: ChangelogCacheType) -> None:
        date = datetime.fromtimestamp(log["timestamp"]).strftime(
            DATE_OUTPUT_FORMAT
        )
        self.out.write(f"Changelog - {date}\n")


def run(args: Namespace) -> None:
    if not args.target:
        args.name, args.password = get_credentials(args.name, args.password)
        args.target = args.name

    cache = Cache(cast(str, args.target))

    if args.sync:
        client = login(args.name, args.password)
        fetched = UserInfo.fetch(client, args.target, args.chunk_size)
        cache.dump_update(fetched)
    elif not cache:
        args.out.write(f"No logs to display for '{args.target}'\n")
        return

    renderer = Renderer(args, cache)
    renderer.render()


def setup_parser(parser: ArgumentParser) -> None:
    parser.add_argument(
        "target",
        nargs="?",
        default="",
        help="The username of the account to log info for",
    )
    parser.add_argument(
        "out",
        nargs="?",
        type=FileType("w", encoding="utf-8"),
        default=stdout,
        help="An optional file to output the logging info",
    )
    parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Display detailed information (i.e. the entire list of followers/followings added/removed)",
    )
    parser.add_argument(
        "--from-date", type=_date_parser, help="Start date (DD-MM-YYYY)"
    )
    parser.add_argument(
        "--to-date", type=_date_parser, help="End date (DD-MM-YYYY)"
    )
    parser.add_argument(
        "--list",
        choices=("followers", "followings"),
        help="Filter by list (only display followers or followings)",
    )
    parser.add_argument(
        "--change",
        choices=("added", "removed"),
        help="Only display 'added' or 'removed' users (applies to each list)",
    )
    parser.add_argument(
        "--username",
        help="Filter by username (only show updates for a specific user)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Include empty logs in the display "
            "(note that some filters make logs be considered empty "
            "such as with '--username' when the user isn't there)"
        ),
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Whether it should (in addition) create a new log by fetching current info",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Only matters if --sync is specified and controls the size of each chunk to fetch while scrapping",
    )
    parser.set_defaults(func=run)
