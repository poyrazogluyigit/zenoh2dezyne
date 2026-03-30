import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description="Generate Dezyne code from a Zenoh C++ applications using Joern")
    parser.add_argument("project_name", help="The name of the project to analyze")
    parser.add_argument("--output", "-o", help="The output directory for generated files", default="generate")
    parser.add_argument("--logging", "-l", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default="WARNING")
    parser.add_argument("--joern-server", help="The URL of the running Joern server (e.g., http://localhost:8080)", default="http://localhost:8080")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.logging.upper(), None), format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug(f"Parsed arguments: {args}")

    from codegen import CodeGenerator
    logging.debug("Starting code generation process")
    codegen = CodeGenerator(args.project_name, args.output, args.joern_server)
    codegen.generate_code()

if __name__ == "__main__":
    main()