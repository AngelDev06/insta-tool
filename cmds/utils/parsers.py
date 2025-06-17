from datetime import date, datetime
from argparse import ArgumentTypeError

def date_parser(argument: str) -> date:
    try:
        return datetime.strptime(argument, "%d-%m-%Y").date()
    except ValueError:
        raise ArgumentTypeError(f"'{argument}' is not a proper date")