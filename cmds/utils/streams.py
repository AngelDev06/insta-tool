from sys import stdout
from typing import TextIO, Iterable
from dataclasses import dataclass
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

    def __getattr__(self, name: str):
        return getattr(self.stream, name)
