import argparse
import logging
from pathlib import Path

from .context import RunContext
from .pipeline import Pipeline
from .preprocess import QuomAmalgamator
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
        "--single-stepper",
        action="store_true",
        help="Generate one shared Step component (default: one Step per unit)",
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
    with JoernClient(args.joern_server, workspace_dir=ctx.workspace_dir) as client:
        Pipeline(
            ctx,
            client=client,
            amalgamator=QuomAmalgamator(),
            middleware=args.middleware,
            single_stepper=args.single_stepper,
        ).run()

    logging.info("Code generation complete")


if __name__ == "__main__":
    main()
