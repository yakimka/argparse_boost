from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from argparse_boost._discovery import (
    Command,
    add_global_arguments,
    discover_commands,
    setup_environment,
)
from argparse_boost._framework import env_loader

if TYPE_CHECKING:
    import argparse
    from types import ModuleType


class Loader(Protocol):
    def __call__(
        self,
        fields: list[tuple[str, ...]],
        config: Config,
    ) -> dict[tuple[str, ...], Any]:
        """
        Callable that loads configuration values.
        """


@dataclass(kw_only=True)
class Config:
    app_name: str = "app"
    env_prefix: str = ""
    env_file: str | None = None
    loaders: list[Loader] = field(default_factory=lambda: [env_loader])
    discover_commands_func: Callable[[ModuleType], dict[str, Command]] = (
        discover_commands
    )
    add_global_arguments_func: Callable[
        [argparse.ArgumentParser],
        argparse.ArgumentParser,
    ] = add_global_arguments
    setup_environment_func: Callable[[argparse.Namespace], argparse.Namespace] = (
        setup_environment
    )
