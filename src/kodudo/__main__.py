"""Kodudo CLI.

Usage:
    kodudo cook <config.yaml> ...
    python -m kodudo cook <config.yaml> ...
"""

import argparse
import sys
from pathlib import Path

from kodudo import KodudoError, __version__, cook


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kodudo - Cook your data into documents using Jinja2 templates",
        prog="kodudo",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Cook command
    cook_parser = subparsers.add_parser("cook", help="Render data using a config file")
    cook_parser.add_argument(
        "configs", type=Path, nargs="+", help="Path to YAML configuration file(s)"
    )

    args = parser.parse_args()

    if args.command == "cook":
        exit_code = 0
        for config_path in args.configs:
            if not config_path.exists():
                print(f"Error: Config file not found: {config_path}", file=sys.stderr)
                exit_code = 1
                continue

            try:
                output_paths = cook(config_path)
                for output_path in output_paths:
                    print(f"Cooked: {output_path}")
            except KodudoError as e:
                print(f"Error processing {config_path}: {e}", file=sys.stderr)
                exit_code = 1

        return exit_code

    if args.command is None:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
