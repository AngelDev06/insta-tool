from datetime import date
from typing import Callable, Iterable, Optional


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
