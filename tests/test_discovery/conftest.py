from collections.abc import Callable

import pytest

from argparse_boost import Config, setup_main
from tests.test_discovery import cli


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
            commands_package=cli,
        )

    return maker
