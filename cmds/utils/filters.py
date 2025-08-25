from argparse import Namespace
from datetime import datetime
from typing import Iterable, Protocol

from .constants import CHANGES, LISTS, ChangesType, ListsType


class WithDateSpecification(Protocol):
    timestamp: datetime


def date_filter[T: WithDateSpecification](
    args: Namespace, iterable: Iterable[T]
) -> Iterable[T]:
    if args.from_date is not None and args.to_date is not None:
        return (
            entry
            for entry in iterable
            if args.from_date <= entry.timestamp.date() <= args.to_date
        )
    if args.from_date is not None:
        return (entry for entry in iterable if entry.timestamp.date() >= args.from_date)
    if args.to_date is not None:
        return (entry for entry in iterable if entry.timestamp.date() <= args.to_date)
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
