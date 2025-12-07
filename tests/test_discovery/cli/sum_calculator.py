import argparse


def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--first",
        type=int,
        required=True,
        help="First number to sum",
    )
    parser.add_argument(
        "--second",
        type=int,
        required=True,
        help="Second number to sum",
    )


def main(args: argparse.Namespace) -> None:
    result = args.first + args.second
    print(f"SUM={result}")
