from argparse import Namespace
from datetime import date, datetime
from typing import Callable, Iterable, Optional, Protocol

from .constants import CHANGES, LISTS, ChangesType, ListsType


def date_filter[T](
    from_date: Optional[date],
    to_date: Optional[date],
    iterable: Iterable[T],
    date_access: Callable[[T], date] = lambda entry: entry.timestamp.date(),
) -> Iterable[T]:
    if from_date is not None and to_date is not None:
        return (
            entry for entry in iterable if from_date <= date_access(entry) <= to_date
        )
    if from_date is not None:
        return (entry for entry in iterable if date_access(entry) >= from_date)
    if to_date is not None:
        return (entry for entry in iterable if date_access(entry) <= to_date)
    return iterable


def list_filter(args: Namespace) -> Iterable[ListsType]:
    if args.list is None:
        return LISTS
    if args.list in LISTS:
        return (args.list,)
    raise RuntimeError("`list` argument is invalid")


def change_filter(args: Namespace) -> Iterable[ChangesType]:
    if args.change is None:
        return CHANGES
    if args.change in CHANGES:
        return (args.change,)
    raise RuntimeError("`change` argument is invalid")
