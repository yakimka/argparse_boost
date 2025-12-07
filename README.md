# argparse-boost

[![Build Status](https://github.com/yakimka/argparse-boost/actions/workflows/workflow-ci.yml/badge.svg?branch=main&event=push)](https://github.com/yakimka/argparse-boost/actions/workflows/workflow-ci.yml)
[![Codecov](https://codecov.io/gh/yakimka/argparse-boost/branch/main/graph/badge.svg)](https://codecov.io/gh/yakimka/argparse-boost)
[![PyPI - Version](https://img.shields.io/pypi/v/argparse-boost.svg)](https://pypi.org/project/argparse-boost/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/argparse-boost)](https://pypi.org/project/picodi/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/argparse-boost)](https://pypi.org/project/picodi/)

argparse-boost is a library for building CLI applications with automatic argument parsing from
dataclasses and environment variable support.

## Installation

```bash
pip install argparse-boost
```

## How to use

### Quick Start: Multi-Command CLI

Build multi-command CLIs (like `git`, `docker`, `kubectl`) with automatic command discovery:

**Project structure:**

```
myapp/
├── __main__.py
└── commands/
    └── greet.py
```

**myapp/__main__.py:**

```python
import os
from argparse_boost import setup_main


def main() -> None:
    setup_main(
        prog="myapp",
        description="My CLI application",
        env_prefix="MYAPP_",
        package_path=os.path.dirname(__file__),
        prefix="myapp.",
    )


if __name__ == "__main__":
    main()
```

**myapp/commands/greet.py:**

```python
from dataclasses import dataclass


@dataclass(kw_only=True)
class GreetConfig:
    name: str
    greeting: str = "Hello"


def main(args: GreetConfig) -> None:
    """Greet someone with a custom message."""
    print(f"{args.greeting}, {args.name}!")
```

**Usage:**

```bash
python -m myapp greet --name World --greeting Hi
# Output: Hi, World!

python -m myapp greet --name Alice
# Output: Hello, Alice!

python -m myapp --help
# Shows available commands

python -m myapp greet --help
# Shows arguments for greet command
```

The library automatically:

- Discovers commands in the `commands/` directory
- Parses arguments from the dataclass type hint in `main()`
- Generates help text from dataclass fields
- Supports environment variables with the specified prefix

### Writing Commands with Dataclass Auto-Parsing

The easiest way to write a command is to use a dataclass type hint in the `main()` function.
Arguments are automatically parsed from the dataclass fields:

```python
from dataclasses import dataclass, field
from typing import Annotated
from argparse_boost import Help


@dataclass(kw_only=True)
class DeployConfig:
    environment: Annotated[str, Help("Target environment (dev/staging/prod)")]
    version: Annotated[str, Help("Version to deploy")]
    dry_run: Annotated[bool, Help("Simulate deployment without making changes")] = False
    services: Annotated[list[str], Help("Services to deploy")] = field(
        default_factory=list
    )


def main(args: DeployConfig) -> None:
    """Deploy application to the specified environment."""
    if args.dry_run:
        print(f"[DRY RUN] Would deploy {args.version} to {args.environment}")
    else:
        print(f"Deploying {args.version} to {args.environment}...")

    if args.services:
        print(f"Services: {', '.join(args.services)}")
```

**Usage:**

```bash
python -m myapp deploy --environment prod --version 1.2.3
python -m myapp deploy --environment staging --version 1.2.4 --dry-run true
python -m myapp deploy --environment dev --version 1.2.5 --services "api,worker"
```

This approach gives you:

- Type-safe argument parsing
- Automatic validation (required fields, type checking)
- Auto-generated help text with descriptions
- Support for complex types (lists, dicts, nested dataclasses)

### Writing Commands with Manual Parser Setup

For more control over argument parsing, use `setup_parser()` and work with `argparse.Namespace`:

```python
import argparse


def setup_parser(parser: argparse.ArgumentParser) -> None:
    """Configure arguments for this command."""
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Target environment",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version to deploy",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force deployment even if validation fails",
    )


def main(args: argparse.Namespace) -> None:
    """Deploy application to the specified environment."""
    print(f"Deploying {args.version} to {args.environment}")
    if args.force:
        print("Force mode enabled - skipping validation")
```

This approach is useful when you need:

- Custom argument behavior (choices, actions, mutual exclusivity)
- Integration with existing argparse code
- Arguments that don't map cleanly to dataclass fields

**Async command support:**
Commands can also be async - the library automatically handles them with `asyncio.run()`:

```python
async def main(args: argparse.Namespace) -> None:
    """Async command example."""
    await some_async_operation()
```

### Configuration Management (Without CLI)

You can use argparse-boost for configuration management in your project, completely separate from
CLI applications. This is useful for web apps, services, or any Python project that needs type-safe
configuration from environment variables:

```python
from dataclasses import dataclass, field
from argparse_boost import env_for_dataclass, from_dict, field_path_to_env_name


@dataclass(kw_only=True)
class DatabaseConfig:
    host: str
    port: int = 5432
    user: str = "postgres"
    password: str
    pool_size: int = 10


@dataclass(kw_only=True)
class AppConfig:
    debug: bool = False
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    allowed_hosts: list[str] = field(default_factory=list)


# Load configuration from environment variables
config_data = env_for_dataclass(
    AppConfig,
    name_maker=field_path_to_env_name(env_prefix="APP_"),
)
config = from_dict(config_data, AppConfig)

# Now use your type-safe config
print(f"Connecting to {config.db.host}:{config.db.port}")
print(f"Debug mode: {config.debug}")
```

**Environment variables:**

```bash
APP_DEBUG=true
APP_DB_HOST=localhost
APP_DB_PORT=5433
APP_DB_PASSWORD=secret
APP_DB_POOL_SIZE=20
APP_ALLOWED_HOSTS=example.com,api.example.com
```

The configuration is loaded with full type conversion:

- `APP_DEBUG=true` → `config.debug = True`
- `APP_DB_PORT=5433` → `config.db.port = 5433`
- `APP_ALLOWED_HOSTS=a,b` → `config.allowed_hosts = ["a", "b"]`

This approach gives you:

- Type-safe configuration with dataclasses
- Automatic type conversion from environment variables
- Support for nested configuration (flattened to ENV vars)
- No CLI overhead - just configuration management

### Core Features

- **[Multi-Command CLI Framework](#quick-start-multi-command-cli)** - Build git-like CLIs with
  automatic command discovery
- **[Dataclass Auto-Parsing](#writing-commands-with-dataclass-auto-parsing)** - Type-safe argument
  parsing from dataclass type hints
- **[Configuration Management](#configuration-management-without-cli)** - Load type-safe config from
  environment variables
- **[Environment Variable Support](#environment-variable-support)** - Auto-merge ENV vars with CLI
  args (CLI takes priority)
- **[Nested Dataclasses](#nested-dataclasses)** - Automatic flattening with intuitive naming
- **[Custom Parsers](#custom-parsers)** - Extend parsing with custom functions via
  `Annotated[T, Parser(func)]`
- **[Type-Safe Parsing](#advanced-types)** - Support for int, float, str, bool, list, dict, Optional
- **[Custom Help Text](#custom-help-text)** - Enhanced help formatting with defaults and ENV var
  display

### Single-Command CLI with BoostedArgumentParser

For simple single-command CLIs, you can use `BoostedArgumentParser` directly without the
multi-command framework:

```python
from dataclasses import dataclass
from argparse_boost import BoostedArgumentParser, from_dict, dict_from_args


@dataclass(kw_only=True)
class Config:
    host: str
    port: int = 5432
    debug: bool = False


parser = BoostedArgumentParser(prog="myapp", env_prefix="APP_")
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args()
config = from_dict(dict_from_args(args, Config), Config)
print(config)
```

**Run it:**

```bash
# Using CLI arguments
python myapp.py --host localhost --port 8080 --debug true

# Using environment variables
APP_HOST=localhost APP_DEBUG=true python myapp.py

# Mix both (CLI takes priority)
APP_PORT=3000 python myapp.py --host localhost --debug true
```

This automatically creates:

- `--host` (required, string)
- `--port` (optional, int, default: 5432)
- `--debug` (optional, bool, default: False)

### Environment Variable Support

When using `BoostedArgumentParser`, environment variables are automatically read before parsing CLI
arguments. CLI arguments always take priority over environment variables.

Environment variable naming:

- CLI option `--host` → ENV var `APP_HOST` (with prefix)
- CLI option `--port` → ENV var `APP_PORT`
- Multi-word options: `--log-level` → `APP_LOG_LEVEL` (dashes become underscores)

**Example:**

```python
from dataclasses import dataclass
from argparse_boost import BoostedArgumentParser, from_dict, dict_from_args


@dataclass(kw_only=True)
class Config:
    host: str
    log_level: str = "INFO"


parser = BoostedArgumentParser(prog="myapp", env_prefix="APP_")
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args()
config = from_dict(dict_from_args(args, Config), Config)
```

**Usage:**

```bash
# Using environment variables only
APP_HOST=localhost APP_LOG_LEVEL=DEBUG python myapp.py

# CLI overrides ENV
APP_HOST=localhost python myapp.py --host production.example.com
# Result: config.host = 'production.example.com'
```

Environment variables are displayed in the help output when they are currently set:

```bash
APP_HOST=localhost python myapp.py --help
# Shows: --host (env: APP_HOST=localhost)

### Nested Dataclasses

Nested dataclasses are automatically flattened into CLI arguments with intuitive naming:

```python
from dataclasses import dataclass, field
from argparse_boost import BoostedArgumentParser, from_dict, dict_from_args


@dataclass(kw_only=True)
class Database:
    host: str
    port: int = 5432
    use_ssl: bool = False


@dataclass(kw_only=True)
class Config:
    name: str
    db: Database = field(default_factory=lambda: Database(host="localhost"))


parser = BoostedArgumentParser(prog="myapp", env_prefix="APP_")
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args()
config = from_dict(dict_from_args(args, Config), Config)
```

Generated CLI arguments:

- `--name` → `config.name`
- `--db-host` → `config.db.host`
- `--db-port` → `config.db.port`
- `--db-use-ssl` → `config.db.use_ssl`

Environment variables:

- `APP_NAME`
- `APP_DB_HOST`
- `APP_DB_PORT`
- `APP_DB_USE_SSL`

Example usage:

```bash
python myapp.py --name myapp --db-host postgres.local --db-port 5433 --db-use-ssl true
```

### Custom Parsers

Use custom parsing functions for specialized types via `Annotated`:

```python
from dataclasses import dataclass
from typing import Annotated
from argparse_boost import BoostedArgumentParser, Parser, from_dict, dict_from_args


def parse_percentage(value: str) -> float:
    """Parse percentage string like '75%' to float 0.75"""
    if isinstance(value, float):
        return value
    return float(value.rstrip("%")) / 100


@dataclass(kw_only=True)
class Config:
    threshold: Annotated[float, Parser(parse_percentage)] = 0.5


parser = BoostedArgumentParser(prog="myapp")
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args(["--threshold", "75%"])
config = from_dict(dict_from_args(args, Config), Config)

print(config.threshold)  # Output: 0.75
```

Custom parsers are useful for:

- Parsing duration strings (e.g., "1h30m" → seconds)
- Parsing file sizes (e.g., "10MB" → bytes)
- Parsing percentages, ratios, or custom formats
- Validating and transforming complex inputs

### Custom Help Text

Add descriptive help text to fields using `Annotated` with `Help`:

```python
from dataclasses import dataclass
from typing import Annotated
from argparse_boost import BoostedArgumentParser, Help, DefaultsHelpFormatter


@dataclass(kw_only=True)
class Config:
    host: Annotated[str, Help("Database host address")]
    timeout: Annotated[int, Help("Connection timeout in seconds")] = 30
    retries: Annotated[int, Help("Number of retry attempts")] = 3


parser = BoostedArgumentParser(
    prog="myapp",
    env_prefix="APP_",
    formatter_class=DefaultsHelpFormatter,  # Shows defaults in help
)
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args(["--help"])
```

`DefaultsHelpFormatter` automatically adds default values and "Required" indicators to help text.

### Advanced Types

#### Lists

Lists are parsed from comma-separated values:

```python
from dataclasses import dataclass, field
from argparse_boost import BoostedArgumentParser, from_dict, dict_from_args


@dataclass(kw_only=True)
class Config:
    tags: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)


parser = BoostedArgumentParser(prog="myapp", env_prefix="APP_")
parser.parse_arguments_from_dataclass(Config)

# CLI usage
args = parser.parse_args(["--tags", "web,api,database", "--ports", "80,443,8080"])
config = from_dict(dict_from_args(args, Config), Config)
print(config.tags)  # ['web', 'api', 'database']
print(config.ports)  # [80, 443, 8080]
```

Environment variable usage:

```bash
APP_TAGS="production,backend" APP_PORTS="3000,8080" python myapp.py
```

#### Dictionaries

Dictionaries are parsed from comma-separated key-value pairs:

```python
from dataclasses import dataclass, field
from argparse_boost import BoostedArgumentParser, from_dict, dict_from_args


@dataclass(kw_only=True)
class Config:
    limits: dict[str, int] = field(default_factory=dict)


parser = BoostedArgumentParser(prog="myapp")
parser.parse_arguments_from_dataclass(Config)

# Use colon or equals for key-value pairs
args = parser.parse_args(["--limits", "daily:100,monthly:3000"])
# or: ['--limits', 'daily=100,monthly=3000']

config = from_dict(dict_from_args(args, Config), Config)
print(config.limits)  # {'daily': 100, 'monthly': 3000}
```

#### Optional Types

Optional fields are supported via `T | None` or `Optional[T]`:

```python
from dataclasses import dataclass
from argparse_boost import BoostedArgumentParser, from_dict, dict_from_args


@dataclass(kw_only=True)
class Config:
    required_field: str
    optional_field: str | None = None
    optional_with_default: int | None = 42


parser = BoostedArgumentParser(prog="myapp")
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args(["--required-field", "value"])
config = from_dict(dict_from_args(args, Config), Config)

print(config.optional_field)  # None
print(config.optional_with_default)  # 42
```

### Programmatic Usage

For more control, use the low-level API:

```python
from dataclasses import dataclass
from argparse_boost import (
    BoostedArgumentParser,
    from_dict,
    dict_from_args,
    env_for_dataclass,
    field_path_to_env_name,
)


@dataclass(kw_only=True)
class Config:
    host: str
    port: int = 5432


parser = BoostedArgumentParser(prog="myapp", env_prefix="APP_")
parser.parse_arguments_from_dataclass(Config)
args = parser.parse_args(["--host", "example.com"])

# Read environment variables
env_data = env_for_dataclass(
    Config,
    name_maker=field_path_to_env_name(env_prefix="APP_"),
)

# Extract CLI arguments
cli_data = dict_from_args(args, Config)

# Merge (CLI overrides ENV)
merged = {**env_data, **cli_data}

# Construct dataclass
config = from_dict(merged, Config)
```

### API Reference

**Framework Functions:**

- `setup_main()` - Entry point for multi-command CLI applications with automatic command discovery

**Configuration Functions:**

- `from_dict(data, dataclass_type)` - Construct dataclass from flat dict
- `env_for_dataclass(dataclass_type, name_maker)` - Read ENV vars to flat dict
- `field_path_to_env_name(env_prefix)` - Create ENV name mapper

**Parser Classes:**

- `BoostedArgumentParser` - Extended ArgumentParser with ENV variable support
- `DefaultsHelpFormatter` - Help formatter showing defaults and required indicators

**Dataclass Parsing:**

- `dict_from_args(args, dataclass_type)` - Extract CLI args to flat dict
- `arg_option_to_env_name(env_prefix)` - Convert CLI option to ENV name

**Annotations:**

- `Parser(func)` - Custom parsing function for `Annotated` fields
- `Help(text)` - Custom help text for `Annotated` fields

**Exceptions:**

- `CliSetupError` - Base exception for CLI setup errors
- `FieldNameConflictError` - Raised when flattened field names collide
- `UnsupportedFieldTypeError` - Raised for unsupported field types

### Supported Types

| Type             | Example                   | CLI Input             | ENV Input               |
|------------------|---------------------------|-----------------------|-------------------------|
| `int`            | `count: int`              | `--count 42`          | `APP_COUNT=42`          |
| `float`          | `ratio: float`            | `--ratio 3.14`        | `APP_RATIO=3.14`        |
| `str`            | `name: str`               | `--name hello`        | `APP_NAME=hello`        |
| `bool`           | `debug: bool`             | `--debug true`        | `APP_DEBUG=yes`         |
| `list[T]`        | `tags: list[str]`         | `--tags a,b,c`        | `APP_TAGS=a,b,c`        |
| `dict[K,V]`      | `limits: dict[str,int]`   | `--limits a:1,b:2`    | `APP_LIMITS=a:1,b:2`    |
| `T \| None`      | `port: int \| None`       | `--port 80`           | `APP_PORT=80`           |
| Nested dataclass | `db: Database`            | `--db-host localhost` | `APP_DB_HOST=localhost` |
| Custom           | `Annotated[T, Parser(f)]` | Custom parsing        | Custom parsing          |

**Type constraints:**

- `list[T]` and `dict[K,V]`: T, K, V must be simple types (int, float, str, bool) or Optional simple
  types
- `Union` is only supported as `Optional[T]` (i.e., `T | None`)
- Generic unions like `str | int` are not supported

**Boolean parsing** accepts (case-insensitive):

- True: `true`, `yes`, `on`, `1`
- False: `false`, `no`, `off`, `0`

### Tips and Best Practices

1. **Use `kw_only=True` for cleaner CLI:**
   ```python
   @dataclass(kw_only=True)  # Forces keyword-only arguments
   class Config:
       host: str
       port: int = 5432
   ```

2. **Use `field(default_factory=...)` for mutable defaults:**
   ```python
   from dataclasses import dataclass, field


   @dataclass(kw_only=True)
   class Config:
       tags: list[str] = field(default_factory=list)  # Good
       # tags: list[str] = []  # Bad - mutable default
   ```

3. **Avoid field name conflicts with nested dataclasses:**
   ```python
   # This will raise FieldNameConflictError:
   @dataclass(kw_only=True)
   class Database:
       password: str


   @dataclass(kw_only=True)
   class Config:
       db_password: str  # Conflicts with db.password when flattened
       db: Database
   ```

4. **Use `env_prefix` to scope environment variables:**
   ```python
   parser = BoostedArgumentParser(prog="myapp", env_prefix="MYAPP_")
   # Prevents conflicts with other apps' ENV vars
   ```

## Development

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. (?) Copy the example settings file and configure your settings:
   ```bash
   cp settings.example.yaml settings.yaml
   ```
3. Build the Docker images:
   ```bash
   docker-compose build
   ```
4. Install dependencies:
   ```bash
   make uv args="sync"
   ```
5. Start the service:
   ```bash
   docker-compose up
   ```

### Making Changes

1. List available `make` commands:
   ```bash
   make help
   ```
2. Check code style with:
   ```bash
   make lint
   ```
3. Run tests using:
   ```bash
   make test
   ```
4. Manage dependencies via uv:
   ```bash
   make uv args="<uv-args>"
   ```
    - For example: `make uv args="add picodi"`

5. For local CI debugging:
   ```bash
   make run-ci
   ```

#### Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) for linting and formatting:

- It runs inside a Docker container by default.
- Optionally, set up hooks locally:
  ```bash
  pre-commit install
  ```

#### Mypy

We use [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking.

It is configured for strictly typed code, so you may need to add type hints to your code.
But don't be very strict, sometimes it's better to use `Any` type.

## License

[MIT](https://github.com/yakimka/argparse-boost/blob/main/LICENSE)

## Credits

This project was generated with [
`yakimka/cookiecutter-pyproject`](https://github.com/yakimka/cookiecutter-pyproject).
