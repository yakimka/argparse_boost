from dataclasses import dataclass


@dataclass(kw_only=True)
class AutoDataclassConfig:
    int_value: int
    str_value: str


def main(args: AutoDataclassConfig) -> None:
    print(f"INT={args.int_value}")
    print(f"STR={args.str_value}")
