from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from argparse_boost import Config, UnsupportedFieldTypeError, construct_dataclass


def test_cant_use_union_fields():
    @dataclass
    class MyConfig:
        value: int | str

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"value": "test"}, config=Config())


def test_cant_use_optional_list():
    @dataclass
    class MyConfig:
        values: list[int] | None = None

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"values": [1, 2, 3]}, config=Config())


def test_cant_use_optional_dict():
    @dataclass
    class MyConfig:
        mapping: dict[str, int] | None = None

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"mapping": {"a": 1}}, config=Config())


def test_cant_use_nested_list():
    @dataclass
    class MyConfig:
        buckets: list[list[int]]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"buckets": [[1, 2], [3, 4]]}, config=Config())


def test_cant_use_list_with_dicts():
    @dataclass
    class MyConfig:
        items: list[dict[str, int]]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"items": [{"a": 1}, {"b": 2}]}, config=Config())


def test_cant_use_nested_dict():
    @dataclass
    class MyConfig:
        mapping: dict[str, dict[str, int]]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(
            MyConfig,
            {"mapping": {"outer": {"inner": 1}}},
            config=Config(),
        )


def test_cant_use_dict_with_lists():
    @dataclass
    class MyConfig:
        data: dict[str, list[int]]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"data": {"numbers": [1, 2, 3]}}, config=Config())


def test_cant_use_unsupported_value_type():
    @dataclass
    class MyConfig:
        data: set[str]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"data": {"1"}}, config=Config())


def test_cant_use_dict_with_unsupported_value_type():
    @dataclass
    class MyConfig:
        data: dict[str, object]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"data": {"key": "value"}}, config=Config())


def test_cant_use_list_with_any():
    @dataclass
    class MyConfig:
        items: list

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"items": [1, "two", 3.0]}, config=Config())


def test_cant_use_dict_with_any():
    @dataclass
    class MyConfig:
        mapping: dict

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(
            MyConfig,
            {"mapping": {"a": 1, "b": "two"}},
            config=Config(),
        )


def test_cant_use_any_field():
    @dataclass
    class MyConfig:
        value: Any

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"value": "some value"}, config=Config())


def test_cant_use_unparameterized_typing_list():
    @dataclass
    class MyConfig:
        items: List

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"items": ["a", "b"]}, config=Config())


def test_cant_use_unparameterized_typing_dict():
    @dataclass
    class MyConfig:
        mapping: Dict

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"mapping": {"a": 1}}, config=Config())


def test_cant_use_dict_with_non_simple_key():
    @dataclass
    class MyConfig:
        mapping: dict[list[int], str]

    with pytest.raises(UnsupportedFieldTypeError):
        construct_dataclass(MyConfig, {"mapping": {1: "one"}}, config=Config())
