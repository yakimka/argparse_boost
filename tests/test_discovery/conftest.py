from collections.abc import Callable
from pathlib import Path

import pytest

from argparse_boost import setup_main

THIS_DIR = Path(__file__).parent


@pytest.fixture()
def make_main():
    def maker(
        args: list[str] | None = None,
        add_global_arguments: Callable | None = None,
    ) -> None:
        kwargs = {}
        if add_global_arguments is not None:
            kwargs["add_global_arguments"] = add_global_arguments
        return setup_main(
            args,
            prog="test",
            env_prefix="TEST_",
            package_path=str(THIS_DIR / "cli"),
            prefix="tests.test_discovery.cli.",
            **kwargs,
        )

    return maker
