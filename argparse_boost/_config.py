from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from argparse_boost._discovery import (
    Command,
    default_add_global_arguments,
    default_discover_commands,
    default_setup_environment,
)
from argparse_boost._framework import env_for_dataclass

if TYPE_CHECKING:
    import argparse


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
    loaders: list[Loader] = field(default_factory=lambda: [env_for_dataclass])
    discover_commands_func: Callable[[str, str], dict[str, Command]] = (
        default_discover_commands
    )
    add_global_arguments_func: Callable[
        [argparse.ArgumentParser],
        argparse.ArgumentParser,
    ] = default_add_global_arguments
    setup_environment_func: Callable[[argparse.Namespace], argparse.Namespace] = (
        default_setup_environment
    )
