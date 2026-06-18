import argparse
import logging
from pathlib import Path

from .context import RunContext
from .pipeline import Pipeline
from .amalgamate import Amalgamator, AmalgamationMode, OnMissing
from .frontend import JoernClient


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser (testable)."""
    parser = argparse.ArgumentParser(
        description="Generate Dezyne code from a Zenoh C++ application using Joern"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to a source directory (required).",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for generated files",
        default=str(Path.cwd() / "out"),
    )
    parser.add_argument(
        "--logging", "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="WARNING",
    )
    parser.add_argument(
        "--joern-server",
        help="URL of the running Joern server",
        default="http://localhost:8080",
    )
    parser.add_argument(
        "--middleware", "-m",
        choices=["zenoh", "ros1", "ros2"],
        default="zenoh",
        help="Pub/sub middleware of the analyzed project (default: zenoh)",
    )
    parser.add_argument(
        "--amalgamation", "-a",
        choices=["source-only", "source+project", "source+all"],
        default="source-only",
        help=(
            "How much to inline when amalgamating each entry point "
            "(default: source-only). "
            "'source-only': inline only headers located inside the source "
            "directory; leave all other includes untouched. "
            "'source+project': also inline non-system headers (\"...\" "
            "includes) resolvable in the search paths; leave <system> "
            "includes alone. "
            "'source+all': inline every resolvable include, including "
            "<angle> headers found in the search paths; unresolvable "
            "system headers are left as-is."
        ),
    )
    parser.add_argument(
        "--on-missing",
        choices=["warn", "fail"],
        default="warn",
        help=(
            "What to do when a non-system (\"...\") include cannot be "
            "resolved in the search paths (default: warn). "
            "'warn': log a warning and leave the #include line in place. "
            "'fail': log an error and abort. "
            "Unresolvable <system> includes are always left as-is and never "
            "trigger this."
        ),
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.logging.upper(), None),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.debug(f"Parsed arguments: {args}")

    # Build RunContext
    ctx = RunContext(
        input_dir=Path(args.input).resolve(),
        output_dir=Path(args.output).resolve(),
    )

    # Run pipeline
    logging.debug("Starting code generation pipeline")
    with JoernClient(args.joern_server) as client:
        Pipeline(
            ctx,
            client=client,
            amalgamator=Amalgamator(),
            middleware=args.middleware,
            mode=AmalgamationMode(args.amalgamation),
            on_missing=OnMissing(args.on_missing),
        ).run()

    logging.info("Code generation complete")


if __name__ == "__main__":
    main()
