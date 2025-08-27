from dataclasses import dataclass
from sys import stdout
from typing import Iterable, Optional, TextIO

from termcolor import colored


@dataclass
class ColoredOutput:
    stream: TextIO
    color: str
    attrs: Iterable[str] = ("bold", "underline")

    def cwrite(self, text: str) -> int:
        if self.stream is stdout:
            return stdout.write(colored(text, self.color, attrs=self.attrs))
        return self.stream.write(text)

    def write(self, text: str) -> int:
        return self.stream.write(text)

    def set_attrs(
        self, *, color: Optional[str] = None, attrs: Optional[Iterable[str]] = None
    ):
        if color is not None:
            self.color = color
        if attrs is not None:
            self.attrs = attrs

    def __getattr__(self, name: str):
        return getattr(self.stream, name)
