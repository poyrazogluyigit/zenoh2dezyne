import argparse
import logging
import os

from .frontend import JoernQueryAPI
from .codegen import CodeGenerator
from .builders import Builder


def main():
    parser = argparse.ArgumentParser(
        description="Generate Dezyne code from a Zenoh C++ application using Joern"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--project", "-p",
        help="Name of an existing Joern project to translate (must already be in the Joern workspace).",
    )
    source.add_argument(
        "--input", "-i",
        help="Path to a source directory. Joern imports it as a new project; the project "
             "name is taken from the directory's basename.",
    )

    parser.add_argument("--output", "-o", help="Output directory for generated files", default="generate")
    parser.add_argument("--logging", "-l", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default="WARNING")
    parser.add_argument("--joern-server", help="URL of the running Joern server", default="http://localhost:8080")
    parser.add_argument(
        "--single-stepper", action="store_true",
        help="Generate one shared Step component (default: one Step per unit)",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.logging.upper(), None),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.debug(f"Parsed arguments: {args}")

    if args.input is not None:
        input_dir = os.path.abspath(args.input)
        project_name = os.path.basename(input_dir.rstrip(os.sep))
    else:
        input_dir = None
        project_name = args.project

    logging.debug("Starting code generation process")
    with JoernQueryAPI(args.joern_server) as api:
        builder = Builder(api)
        graph = builder.buildProject(project_name, input_dir=input_dir)
        codegen = CodeGenerator(args.output)
        codegen.generate(graph, single_stepper=args.single_stepper)
        codegen.printToOutput()


if __name__ == "__main__":
    main()
