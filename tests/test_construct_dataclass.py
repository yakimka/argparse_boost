import re
from dataclasses import MISSING, dataclass, field, fields
from typing import ClassVar

import pytest

from argparse_boost import Config, UnsupportedFieldTypeError, construct_dataclass


def test_unsupported_atom_type_is_reported():
    @dataclass
    class MyConfig:
        payload: object

    with pytest.raises(
        UnsupportedFieldTypeError,
        match=re.escape("Unsupported field type for 'payload': <class 'object'>"),
    ):
        construct_dataclass(MyConfig, {"payload": "value"}, config=Config())


def test_float_and_bool_values_are_parsed():
    @dataclass
    class MyConfig:
        ratio: float
        enabled: bool
        disabled: bool

    parsed = construct_dataclass(
        MyConfig,
        {"ratio": "3.5", "enabled": True, "disabled": "no"},
        config=Config(),
    )

    assert parsed.ratio == pytest.approx(3.5)
    assert parsed.enabled is True
    assert parsed.disabled is False


def test_none_type_rejects_unparsable_string():
    @dataclass
    class MyConfig:
        marker: None

    with pytest.raises(UnsupportedFieldTypeError, match="Cannot parse None"):
        construct_dataclass(MyConfig, {"marker": "nope"}, config=Config())


def test_list_parses_brackets_and_empty_content():
    @dataclass
    class MyConfig:
        numbers: list[int]

    parsed = construct_dataclass(MyConfig, {"numbers": "[]"}, config=Config())

    assert parsed.numbers == []


def test_dict_parses_empty_and_colon_separated_pairs():
    @dataclass
    class MyConfig:
        mapping: dict[str, int]

    empty = construct_dataclass(MyConfig, {"mapping": "   "}, config=Config())
    assert empty.mapping == {}

    parsed = construct_dataclass(MyConfig, {"mapping": "foo:1,bar:2"}, config=Config())
    assert parsed.mapping == {"foo": 1, "bar": 2}

    with pytest.raises(UnsupportedFieldTypeError, match="Cannot parse dict item"):
        construct_dataclass(MyConfig, {"mapping": "foo-1"}, config=Config())


def test_missing_value_for_non_optional_field_errors():
    @dataclass
    class MyConfig:
        count: int

    with pytest.raises(UnsupportedFieldTypeError, match="Missing value"):
        construct_dataclass(MyConfig, {"count": None}, config=Config())


def test_nested_dataclass_requires_mapping():
    @dataclass
    class Child:
        value: int

    @dataclass
    class MyConfig:
        child: Child

    with pytest.raises(UnsupportedFieldTypeError, match="Expected mapping"):
        construct_dataclass(MyConfig, {"child": "value"}, config=Config())


def test_non_optional_union_is_rejected():
    @dataclass
    class MyConfig:
        value: int | str

    with pytest.raises(
        UnsupportedFieldTypeError,
        match=re.escape("Unsupported field type for 'value': int | str"),
    ):
        construct_dataclass(MyConfig, {"value": "1"}, config=Config())


def test_default_factory_and_missing_detection():
    @dataclass
    class FactoryDefault:
        items: list[int] = field(default_factory=list)

    @dataclass
    class RequiredOnly:
        required: int

    # take_default is exercised internally by construct_dataclass(parse_dataclass)
    assert construct_dataclass(FactoryDefault, {}, config=Config()).items == []

    required_field = fields(RequiredOnly)[0]
    assert required_field.default is MISSING


def test_optional_field_set_to_none_when_missing():
    @dataclass
    class MyConfig:
        token: str | None

    parsed = construct_dataclass(MyConfig, {}, config=Config())

    assert parsed.token is None


def test_nested_dataclass_without_prefix_is_parsed():
    @dataclass
    class Child:
        enabled: bool = False

    @dataclass
    class Parent:
        child: Child

    parsed = construct_dataclass(Parent, {}, config=Config())

    assert parsed.child == Child(enabled=False)


def test_missing_required_field_raises_key_error():
    @dataclass
    class MyConfig:
        name: str

    with pytest.raises(KeyError, match="Missing required configuration key: name"):
        construct_dataclass(MyConfig, {}, config=Config())


def test_classvar_fields_are_ignored():
    @dataclass
    class MyConfig:
        version: ClassVar[int | str] = 1
        value: int

    my_config = construct_dataclass(
        MyConfig,
        {"value": "7", "version": "42"},
        config=Config(),
    )

    assert my_config.value == 7
    assert MyConfig.version == 1
