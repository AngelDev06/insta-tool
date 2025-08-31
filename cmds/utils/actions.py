from argparse import Action, ArgumentParser, Namespace
from typing import Any, Optional, Sequence, Union

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
