from dataclasses import dataclass

import pytest

from argparse_boost import Config, construct_dataclass


@pytest.mark.parametrize(
    "data",
    [
        {"name": None},
        {"name": "null"},
        {"name": "NULL"},
        {"name": "Null"},
        {"name": "None"},
    ],
)
def test_can_parse_none_field(data):
    @dataclass
    class MyConfig:
        name: None

    parsed = construct_dataclass(MyConfig, data, config=Config())

    assert parsed.name is None


def test_can_parse_value_for_optional_field():
    @dataclass
    class MyConfig:
        age: int | None

    parsed = construct_dataclass(MyConfig, {"age": 42}, config=Config())

    assert parsed.age == 42


@pytest.mark.parametrize(
    "data",
    [
        {"name": None},
        {"name": "null"},
        {"name": "NULL"},
        {"name": "Null"},
        {"name": "None"},
    ],
)
def test_can_parse_none_for_optional_field(data):
    @dataclass
    class MyConfig:
        name: int | None

    parsed = construct_dataclass(MyConfig, data, config=Config())

    assert parsed.name is None


def test_can_parse_string_none_for_optional_string_field():
    @dataclass
    class MyConfig:
        name: str | None

    parsed = construct_dataclass(MyConfig, {"name": "null"}, config=Config())

    assert parsed.name is None


@pytest.mark.parametrize(
    "data",
    [
        {"name": [None, "Alice", "Bob", None]},
        {"name": "None,Alice,Bob,NULL"},
    ],
)
def test_can_parse_optional_value_from_list_of_strings(data):
    @dataclass
    class MyConfig:
        name: list[str | None]

    parsed = construct_dataclass(MyConfig, data, config=Config())

    assert parsed.name == [None, "Alice", "Bob", None]


@pytest.mark.parametrize(
    "data",
    [
        {"scores": {"alice": None, "bob": "2", "carol": 3}},
        {"scores": "alice=None,bob=2,carol=3"},
    ],
)
def test_can_parse_optional_value_from_dict_of_ints(data):
    @dataclass
    class MyConfig:
        scores: dict[str, int | None]

    parsed = construct_dataclass(MyConfig, data, config=Config())

    assert parsed.scores == {"alice": None, "bob": 2, "carol": 3}
