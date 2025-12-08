from collections.abc import Callable
from pathlib import Path

import pytest

from argparse_boost import Config, setup_main

THIS_DIR = Path(__file__).parent


@pytest.fixture()
def make_main():
    def maker(
        args: list[str] | None = None,
        add_global_arguments: Callable | None = None,
    ) -> None:
        config = Config(
            app_name="test",
            env_prefix="TEST_",
        )
        if add_global_arguments is not None:
            config.add_global_arguments_func = add_global_arguments
        return setup_main(
            args,
            config=config,
            package_path=str(THIS_DIR / "cli"),
            prefix="tests.test_discovery.cli.",
        )

    return maker
