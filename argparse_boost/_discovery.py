from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import pkgutil
import sys
from collections.abc import Callable
from dataclasses import dataclass, is_dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, get_origin, get_type_hints

from argparse_boost._argument_parser import BoostedArgumentParser, BoostedHelpFormatter
from argparse_boost._framework import dict_from_args
from argparse_boost._parsers import from_dict

if TYPE_CHECKING:
    import argparse
    from types import ModuleType

    from argparse_boost._config import Config


logger = logging.getLogger("argparse_boost")

LOG_LEVEL_CHOICES = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET")


class ParameterType(Enum):
    """Type of parameter expected by command main function."""

    NONE = auto()  # main() with no parameters
    NAMESPACE = auto()  # main(args: argparse.Namespace)
    DATACLASS = auto()  # main(args: SomeDataclass)


@dataclass
class Command:
    """Metadata for discovered command."""

    name: str
    module_name: str
    entry_point: Callable[[argparse.Namespace], Any]
    setup_parser: Callable[[argparse.ArgumentParser], None] | None
    is_async: bool
    doc: str | None
    parameter_type: ParameterType
    dataclass_type: type[Any] | None


def _inspect_main_signature(
    main_func: Callable[..., Any],
) -> tuple[ParameterType, type[Any] | None]:
    """
    Inspect the signature of a main() function to determine parameter type.

    Returns:
        Tuple of (ParameterType, dataclass_type or None)

    Strategy:
        - Look through all parameters to find the first dataclass parameter
        - If found, return DATACLASS with the dataclass type
        - If no dataclass found but has parameters, return NAMESPACE
        - If no parameters, return NONE
        - If main() has additional required params, Python will raise TypeError at runtime
    """
    sig = inspect.signature(main_func)
    params = [
        p
        for p in sig.parameters.values()
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.KEYWORD_ONLY,
        )
    ]

    if len(params) == 0:
        return ParameterType.NONE, None

    try:
        hints = get_type_hints(main_func)
    except Exception:  # noqa: BLE001
        hints = {}

    for param in params:
        if param.annotation is inspect.Parameter.empty:
            annotation = hints.get(param.name)
        else:
            annotation = hints.get(param.name, param.annotation)

        if annotation is None:
            continue

        # Skip generic types (can't be dataclass)
        if get_origin(annotation) is not None:
            continue

        if inspect.isclass(annotation) and is_dataclass(annotation):
            return ParameterType.DATACLASS, annotation

    return ParameterType.NAMESPACE, None


def discover_commands(commands_package: ModuleType) -> dict[str, Command]:
    """
    Discover all command modules in package.

    Args:
        commands_package: Package module to scan for commands

    Returns:
        Dict mapping command name -> Command metadata

    Raises:
        AttributeError: If commands_package doesn't have __path__ attribute (not a package)
        ValueError: If commands_package has empty __path__

    Discovery rules:
    - Module must be in specified package
    - Module name cannot start with '_'
    - Module name cannot be '__init__' or '__main__'
    - Module must have main() function
    - Module may optionally have setup_parser() function
    - Modules that fail to import or expose invalid setup_parser() are skipped with a warning
    """
    if not hasattr(commands_package, "__path__"):
        msg = (
            f"Module {commands_package.__name__!r} is not a package. "
            "Only package modules with __path__ can be used for command discovery."
        )
        raise AttributeError(msg)

    if not commands_package.__path__:
        msg = f"Package {commands_package.__name__!r} has empty __path__."
        raise ValueError(msg)

    package_path = commands_package.__path__[0]
    prefix = f"{commands_package.__name__}."

    commands: dict[str, Command] = {}
    for module_info in pkgutil.iter_modules([package_path], prefix=prefix):
        module_name = module_info.name.split(".")[-1]

        # Skip private modules and special files
        if module_name.startswith("_"):
            continue

        try:
            module = importlib.import_module(module_info.name)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to import module %s", module_info.name, exc_info=e)
            continue

        main_func = getattr(module, "main", None)
        if not main_func:
            logger.warning("No entry point in %s, skipping", module_info.name)
            continue

        parameter_type, dataclass_type = _inspect_main_signature(main_func)

        setup_parser_func = getattr(module, "setup_parser", None)
        if setup_parser_func and not callable(setup_parser_func):
            logger.warning("%s.setup_parser is not callable, skipping", module_name)
            continue

        commands[module_name] = Command(
            name=module_name,
            module_name=module_info.name,
            entry_point=main_func,
            setup_parser=setup_parser_func,
            is_async=asyncio.iscoroutinefunction(main_func),
            doc=inspect.getdoc(module) or None,
            parameter_type=parameter_type,
            dataclass_type=dataclass_type,
        )

    return commands


def add_global_arguments(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Attach arguments that are shared across all subcommands."""
    global_group = parser.add_argument_group("Global parameters")
    global_group.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        choices=LOG_LEVEL_CHOICES,
        help="Logging level for CLI output.",
    )
    return parser


def register_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    commands: dict[str, Command],
    add_globals: (
        Callable[[argparse.ArgumentParser], argparse.ArgumentParser] | None
    ) = None,
) -> None:
    """
    Register discovered commands in argparse subparsers.

    Args:
        subparsers: ArgumentParser subparsers object
        commands: Dict of discovered commands
        add_globals: Optional callback to register global CLI arguments on each subparser
    """
    for name, command in commands.items():
        # Get first line of docstring for help
        help_text = command.doc.split("\n")[0] if command.doc else ""

        # Create subparser for this command
        subparser = subparsers.add_parser(
            name,
            help=help_text,
            description=command.doc,
            formatter_class=BoostedHelpFormatter,
        )

        # Auto-register dataclass arguments if needed
        if command.parameter_type == ParameterType.DATACLASS:
            if command.dataclass_type is None:
                logger.error(
                    "Command %s has DATACLASS parameter type but no dataclass_type set",
                    name,
                )
                continue
            if hasattr(subparser, "parse_arguments_from_dataclass"):
                subparser.parse_arguments_from_dataclass(command.dataclass_type)
            else:
                logger.warning(
                    "Subparser for %s doesn't support parse_arguments_from_dataclass",
                    name,
                )

        # Let command register its arguments
        if command.setup_parser:
            command.setup_parser(subparser)

        # Append global arguments at the end of help output
        if add_globals:
            add_globals(subparser)

        # Link subparser to command (will be used in main)
        subparser.set_defaults(_command=command)


def run_command(command: Command, args: argparse.Namespace) -> None:
    """
    Execute a command with parsed arguments.

    Args:
        command: Command metadata
        args: Parsed arguments

    Raises:
        Any exception raised by the command
    """
    call_args: tuple[Any, ...]
    if command.parameter_type == ParameterType.NONE:
        call_args = ()
    elif command.parameter_type == ParameterType.DATACLASS:
        if command.dataclass_type is None:
            msg = f"Command {command.name} has DATACLASS type but no dataclass_type"
            raise ValueError(msg)

        parsed = dict_from_args(args, command.dataclass_type)
        data = {"_".join(k): v for k, v in parsed.items() if v is not None}
        dataclass_instance = from_dict(command.dataclass_type, data)
        call_args = (dataclass_instance,)
    else:
        # Pass Namespace as-is
        call_args = (args,)

    if command.is_async:
        asyncio.run(command.entry_point(*call_args))
    else:
        command.entry_point(*call_args)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for CLI commands."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def setup_environment(args: argparse.Namespace) -> argparse.Namespace:
    """Global initialization: logging, Sentry, etc."""
    setup_logging(getattr(args, "log_level", "INFO"))
    # Future: Sentry initialization
    return args


def setup_cli(
    args: list[str] | None = None,
    *,
    config: Config,
    description: str = "",
    commands_package: ModuleType,
) -> None:
    """
    Main entry point for CLI with automatic command discovery.

    Args:
        args: Command-line arguments to parse (defaults to sys.argv)
        config: Configuration object with app settings
        description: Description text for the CLI application
        commands_package: Package module containing command modules to discover

    Raises:
        AttributeError: If commands_package is not a package module
    """
    commands = config.discover_commands_func(commands_package)

    parser = BoostedArgumentParser(
        prog=config.app_name,
        description=description,
        formatter_class=BoostedHelpFormatter,
        env_prefix=config.env_prefix,
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        required=True,
    )

    register_commands(
        subparsers,
        commands,
        add_globals=config.add_global_arguments_func,
    )

    config.add_global_arguments_func(parser)

    parsed_args = parser.parse_args(args)

    config.setup_environment_func(parsed_args)

    command = parsed_args._command  # noqa: SLF001

    try:
        run_command(command, parsed_args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        raise SystemExit(130) from None
