from argparse import ArgumentParser, Namespace
from termcolor import cprint
from ...models import cached
from ...utils.parsers import id_or_date
from ...utils.bots import Bot


def run(args: Namespace):
    bot = Bot.get(args.name, args.password, args.tfa_seed)
    args.name = bot.username

    records = cached.StoryHistory.get(args.name)

    if not records.delete(args.name, args.record):
        cprint("No record was deleted", "red", attrs=("bold", "underline"))
        return
    cprint(
        "Record was deleted successfully", "green", attrs=("bold", "underline")
    )


def setup_parser(parser: ArgumentParser):
    parser.add_argument(
        "record",
        type=id_or_date,
        help="Date (DD-MM-YYYY) or story ID of the record "
        "to delete. If a date is provided and multiple records "
        "exist for that date then a user prompt will determine "
        "which one to delete",
    )
    parser.set_defaults(subfunc2=run)
