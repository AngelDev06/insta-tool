from argparse import Namespace
from typing import Iterable, Union, Literal, TypeAlias
from datetime import date
from .cache import ChangelogCacheType

ListFilterRetType: TypeAlias = Union[
    tuple[Literal["followers"]],
    tuple[Literal["followings"]],
    tuple[Literal["followers"], Literal["followings"]],
]
ChangeFilterRetType: TypeAlias = Union[
    tuple[Literal["added"]],
    tuple[Literal["removed"]],
    tuple[Literal["added"], Literal["removed"]],
]


def date_filter(
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


def list_filter(args: Namespace) -> ListFilterRetType:
    if args.list is None:
        return ("followers", "followings")
    if args.list == "followers":
        return ("followers",)
    return ("followings",)


def change_filter(args: Namespace) -> ChangeFilterRetType:
    if args.change is None:
        return ("added", "removed")
    if args.change == "added":
        return ("added",)
    return ("removed",)
