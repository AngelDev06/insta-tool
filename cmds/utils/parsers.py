from argparse import ArgumentTypeError
from datetime import date, datetime
from typing import Union


def date_parser(argument: str) -> date:
    try:
        return datetime.strptime(argument, "%d-%m-%Y").date()
    except ValueError:
        raise ArgumentTypeError(f"'{argument}' is not a proper date")


def id_or_date(argument: str) -> Union[date, int]:
    try:
        return int(argument)
    except ValueError:
        pass
    try:
        return datetime.strptime(argument, "%d-%m-%Y").date()
    except ValueError:
        raise ArgumentTypeError(f"'{argument}' is neither a proper date nor an id")


def username_with_id(argument: str) -> tuple[int, str]:
    items = argument.split("-")

    if len(items) == 1:
        return (0, argument)

    return (int(items[1]), items[0])
