import argparse


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--flag", action="store_true")
