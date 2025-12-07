import argparse


def setup_parser(parser: argparse.ArgumentParser) -> None:
    pass


def main(args: argparse.Namespace) -> None:  # noqa: ARG001
    print("Hello from private module!")
