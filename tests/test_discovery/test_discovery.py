import pytest


def test_run_sync_command(make_main, capsys) -> None:
    make_main(["sum_calculator", "--first", "2", "--second", "3"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "SUM=5"


def test_run_async_command(make_main, capsys) -> None:
    make_main(["sum_calculator_async", "--first", "2", "--second", "3"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "SUM=5"


def test_commands_with_leading_underscore_are_not_discovered(make_main, capsys) -> None:
    with pytest.raises(SystemExit):
        make_main(["_private_module"])

    captured = capsys.readouterr()
    assert "invalid choice: '_private_module'" in captured.err


def test_discovery_skips_modules_with_import_errors(make_main, capsys, caplog) -> None:
    caplog.set_level("WARNING", logger="argparse_boost")

    make_main(["valid_no_setup_parser"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "VALID"
    assert any(
        "Failed to import module tests.test_discovery.cli.broken_import" in message
        for message in caplog.messages
    )


def test_modules_without_main_are_not_registered(make_main, capsys, caplog) -> None:
    caplog.set_level("WARNING", logger="argparse_boost")

    with pytest.raises(SystemExit):
        make_main(["missing_main"])

    captured = capsys.readouterr()
    assert "invalid choice: 'missing_main'" in captured.err
    assert any(
        "No entry point in tests.test_discovery.cli.missing_main" in message
        for message in caplog.messages
    )


def test_non_callable_setup_parser_is_skipped(make_main, capsys, caplog) -> None:
    caplog.set_level("WARNING", logger="argparse_boost")

    make_main(["sum_calculator", "--first", "1", "--second", "2"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "SUM=3"
    assert any(
        "bad_setup_parser.setup_parser is not callable" in message
        for message in caplog.messages
    )

    with pytest.raises(SystemExit):
        make_main(["bad_setup_parser"])

    captured = capsys.readouterr()
    assert "invalid choice: 'bad_setup_parser'" in captured.err


def test_add_global_arguments_called_for_subparsers(make_main) -> None:
    calls: list[str] = []

    def add_global_arguments(parser):
        calls.append(parser.prog)
        parser.add_argument("--dummy", action="store_true")
        return parser

    make_main(
        ["sum_calculator", "--first", "2", "--second", "2"],
        add_global_arguments=add_global_arguments,
    )

    assert calls  # ensure branch executed
    assert len(calls) >= 5  # main parser + discovered commands


def test_command_without_setup_parser_runs(make_main, capsys) -> None:
    make_main(["valid_no_setup_parser"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "VALID"


def test_keyboard_interrupt_results_in_exit_code_130(make_main, capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        make_main(["keyboard_interrupt"])

    assert excinfo.value.code == 130

    captured = capsys.readouterr()
    assert "Interrupted" in captured.err


def test_main_with_dataclass_argument_gets_parsed_automatically(
    make_main,
    capsys,
) -> None:
    make_main(["auto_dataclass_args", "--int-value", "42", "--str-value", "hello"])

    captured = capsys.readouterr()
    assert "INT=42" in captured.out
    assert "STR=hello" in captured.out


def test_main_without_arguments_runs_successfully(make_main, capsys) -> None:
    make_main(["no_args_command"])

    captured = capsys.readouterr()
    assert captured.out.strip() == "NO_ARGS_COMMAND_OUTPUT"
