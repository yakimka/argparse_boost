from dataclasses import dataclass, field
from typing import Annotated

import pytest

from argparse_boost import (
    BoostedArgumentParser,
    BoostedHelpFormatter,
    Config,
    Help,
    Parser,
    construct_dataclass,
    dict_from_args,
)


@pytest.fixture()
def env_prefix():
    return "APP_"


@pytest.fixture()
def parser(env_prefix):
    return BoostedArgumentParser(prog="test", env_prefix=env_prefix)


def test_cli_parsing_supports_list_with_comma(parser):
    @dataclass(kw_only=True)
    class MyConfig:
        tags: list[str]

    parser.parse_arguments_from_dataclass(MyConfig)
    args = parser.parse_args(["--tags", "one,two,three"])

    merged = dict_from_args(args, MyConfig)
    flat_data = {"_".join(k): v for k, v in merged.items()}
    my_config = construct_dataclass(MyConfig, flat_data, config=Config())

    assert my_config.tags == ["one", "two", "three"]


def test_applies_defaults_and_optionals(parser):
    @dataclass(kw_only=True)
    class Nested:
        value: str = "fallback"

    @dataclass(kw_only=True)
    class MyConfig:
        required: int
        optional_value: int | None = None
        with_default: str = "default"
        nested: Nested = field(default_factory=Nested)

    parser.parse_arguments_from_dataclass(MyConfig)
    args = parser.parse_args(["--required", "10"])

    merged = dict_from_args(args, MyConfig)
    flat_data = {"_".join(k): v for k, v in merged.items()}
    my_config = construct_dataclass(MyConfig, flat_data, config=Config())

    assert my_config.required == 10
    assert my_config.optional_value is None
    assert my_config.with_default == "default"
    assert my_config.nested.value == "fallback"


def test_cli_values_override_env(monkeypatch):
    @dataclass(kw_only=True)
    class AppConfig:
        name: str

    parser = BoostedArgumentParser(prog="test", env_prefix="APP_")
    parser.parse_arguments_from_dataclass(AppConfig)
    monkeypatch.setenv("APP_NAME", "env-name")

    args = parser.parse_args(["--name", "cli-name"])

    assert args.name == "cli-name"


def test_invalid_bool_from_cli_raises():
    @dataclass(kw_only=True)
    class Config:
        enabled: bool

    parser = BoostedArgumentParser(prog="test", env_prefix="APP_")
    parser.parse_arguments_from_dataclass(Config)

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--enabled", "not-a-bool"])

    assert exc_info.value.code == 2


def test_required_field_missing_triggers_system_exit(parser):
    @dataclass(kw_only=True)
    class Config:
        required: int

    parser.parse_arguments_from_dataclass(Config)

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([])

    assert exc_info.value.code == 2


def test_help_includes_default_value_from_dataclass():
    @dataclass(kw_only=True)
    class Config:
        threshold: Annotated[int, Help("Example threshold.")] = 42

    parser = BoostedArgumentParser(
        prog="test",
        env_prefix="APP_",
        formatter_class=BoostedHelpFormatter,
    )
    parser.parse_arguments_from_dataclass(Config)

    help_text = parser.format_help()

    assert "--threshold" in help_text
    assert "Default: 42" in help_text


def _double_int(value: str) -> int:
    return int(value) * 2


def test_dataclass_cli_and_env_merge_into_nested_config(monkeypatch):
    @dataclass(kw_only=True)
    class Database:
        host: str
        port: int = 5432
        use_ssl: bool = False

    @dataclass(kw_only=True)
    class AppConfig:
        name: str
        tags: list[str] = field(default_factory=list)
        limits: dict[str, int] = field(default_factory=dict)
        multiplier: Annotated[int, Parser(_double_int)] = 1
        note: Annotated[str, Help("Optional note.")] = "n/a"
        db: Database = field(
            default_factory=lambda: Database(host="localhost"),
        )

    parser = BoostedArgumentParser(prog="test", env_prefix="APP_")
    parser.parse_arguments_from_dataclass(AppConfig)
    monkeypatch.setenv("APP_DB_HOST", "env-db.local")
    monkeypatch.setenv("APP_LIMITS", "daily=5,monthly=10")
    monkeypatch.setenv("APP_NOTE", "from-env")
    monkeypatch.setenv("APP_MULTIPLIER", "3")

    args = parser.parse_args(
        [
            "--name",
            "cli-name",
            "--db-port",
            "15432",
            "--db-use-ssl",
            "true",
            "--tags",
            "blue,green",
        ],
    )

    assert args.name == "cli-name"
    assert args.db_host == "env-db.local"
    assert args.db_port == "15432"
    assert args.db_use_ssl == "true"
    assert args.tags == "blue,green"
    assert args.limits == "daily=5,monthly=10"
    assert args.multiplier == "3"
    assert args.note == "from-env"
