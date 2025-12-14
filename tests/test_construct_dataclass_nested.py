from dataclasses import dataclass

from argparse_boost import Config, construct_dataclass


def test_parse_nested_dataclass_from_flat_dict_keys():
    @dataclass
    class DBConfig:
        url: str

    @dataclass
    class MyConfig:
        db: DBConfig

    my_config = construct_dataclass(
        MyConfig,
        {"db_url": "sqlite:///test.db"},
        config=Config(),
    )
    assert my_config.db.url == "sqlite:///test.db"


def test_parse_nested_dataclass_from_dataclass():
    @dataclass
    class DBConfig:
        url: str

    @dataclass
    class MyConfig:
        db: DBConfig

    my_config = construct_dataclass(
        MyConfig,
        {"db": DBConfig(url="sqlite:///test.db")},
        config=Config(),
    )
    assert my_config.db.url == "sqlite:///test.db"


def test_parse_nested_dataclass_from_dict():
    @dataclass
    class DBConfig:
        url: str

    @dataclass
    class MyConfig:
        db: DBConfig

    my_config = construct_dataclass(
        MyConfig,
        {"db": {"url": "sqlite:///test.db"}},
        config=Config(),
    )
    assert my_config.db.url == "sqlite:///test.db"
