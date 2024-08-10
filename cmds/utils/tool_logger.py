import logging

from termcolor import colored


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "green",
        logging.INFO: "blue",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "light_red",
    }

    def format(self, record: logging.LogRecord):
        return colored(super().format(record), self.COLORS[record.levelno])


logger = logging.getLogger("insta-tool-logger")


def setup(debug: bool):
    if logger.hasHandlers():
        return
    logger.propagate = False
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter(
            fmt="[%(levelname)s] (%(asctime)s) %(name)s: %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )
    )
    logger.addHandler(handler)
