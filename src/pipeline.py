import logging
from dataclasses import dataclass, field
from pathlib import Path

from .context import RunContext
from .preprocess import detect_nodes, Amalgamator
from .frontend import JoernClient
from .builders import Builder, InterconnectionGraph
from .codegen import CodeGenerator

logger = logging.getLogger(__name__)


@dataclass
class Pipeline:
    """Orchestrates the full preprocessing pipeline: detect, amalgamate, import,
    build, codegen, and write.

    Attributes:
        ctx: RunContext providing input/output paths.
        client: JoernClient for code analysis.
        amalgamator: Amalgamator for merging source files.
        middleware: Middleware name for extraction ("zenoh", "ros1", "ros2", ...).
        nodes: List of detected .cpp files defining main().
        graph: InterconnectionGraph built from code analysis.
        codegen: CodeGenerator instance for Dezyne output.
    """
    ctx: RunContext
    client: JoernClient
    amalgamator: Amalgamator
    middleware: str = "zenoh"
    nodes: list[Path] = field(default_factory=list)
    graph: InterconnectionGraph | None = None
    codegen: CodeGenerator | None = None

    def run(self) -> None:
        """Execute all pipeline stages in order."""
        for stage in STAGES:
            logger.info("pipeline stage: %s", stage.__name__)
            stage(self)


def _detect(p: Pipeline) -> None:
    """Stage 1: Detect entry points (files defining main()) and create output dirs."""
    p.ctx.mkdirs()
    p.nodes = detect_nodes(p.ctx.input_dir)


def _amalgamate(p: Pipeline) -> None:
    """Stage 2: Amalgamate each node's dependencies into a single file."""
    dirs = [p.ctx.input_dir, *(d for d in p.ctx.input_dir.rglob("*") if d.is_dir())]
    for node in p.nodes:
        p.amalgamator.amalgamate(node, p.ctx.amalgamated_dir / node.name, dirs)


def _import(p: Pipeline) -> None:
    """Stage 3: Import amalgamated code into Joern project."""
    p.client.delete_project(p.ctx.project_name)
    p.client.import_code(str(p.ctx.amalgamated_dir), p.ctx.project_name)


def _build(p: Pipeline) -> None:
    """Stage 4: Build interconnection graph from code analysis."""
    p.graph = Builder(p.client).build(p.middleware)


def _codegen(p: Pipeline) -> None:
    """Stage 5: Generate Dezyne code from interconnection graph."""
    p.codegen = CodeGenerator(str(p.ctx.models_dir))
    p.codegen.generate(p.graph)


def _write(p: Pipeline) -> None:
    """Stage 6: Write generated Dezyne files to disk."""
    p.codegen.printToOutput()


STAGES = [_detect, _amalgamate, _import, _build, _codegen, _write]
