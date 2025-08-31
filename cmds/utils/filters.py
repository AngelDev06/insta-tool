from argparse import Namespace
from datetime import date
from typing import Callable, Collection, Iterable, Optional

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


def list_filter(list_name: Optional[ListsType]) -> Collection[ListsType]:
    if list_name is None:
        return LISTS
    if list_name in LISTS:
        return (list_name,)
    raise RuntimeError("`list` argument is invalid")


def change_filter(change_type: Optional[ChangesType]) -> Collection[ChangesType]:
    if change_type is None:
        return CHANGES
    if change_type in CHANGES:
        return (change_type,)
    raise RuntimeError("`change` argument is invalid")
