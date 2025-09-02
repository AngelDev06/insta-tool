from argparse import Action, ArgumentParser, FileType, Namespace
from collections.abc import Callable
from typing import Any, Iterable, Optional, Sequence, Union

from .bots import Config


class StoreInConfig(Action):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Optional[Union[str, Sequence[Any]]],
        option_string: Optional[str] = None,
    ) -> None:
        config = Config.get()
        setattr(config, self.dest, values)
        setattr(namespace, self.dest, values)
        config.backup()


class UniqueChoices(Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        nargs: Union[str, int],
        **kwargs,
    ) -> None:
        if nargs is None:
            raise ValueError("nargs must be specified")
        if isinstance(nargs, int):
            if nargs <= 1:
                raise ValueError(
                    "argument must accept at least 2 items (i.e. nargs > 1)"
                )
        elif isinstance(nargs, str):
            if nargs == "?":
                raise ValueError("nargs can't be ?")
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Optional[Union[str, Sequence[Any]]],
        option_string: Optional[str] = None,
    ) -> None:
        if values is None:
            setattr(namespace, self.dest, values)
            return
        setattr(namespace, self.dest, list(dict.fromkeys(values)))
