import argparse
import asyncio

from .server import serve

__version__ = "0.1.0"


def main() -> None:
    """MCP TDO Server - Note taking and task management functionality."""
    parser = argparse.ArgumentParser(
        description="give a model the ability to work with tdo notes and todos"
    )
    parser.add_argument("--tdo-path", type=str, help="Path to the tdo script")

    args = parser.parse_args()
    asyncio.run(serve(args.tdo_path))


if __name__ == "__main__":
    main()
