from dataclasses import dataclass, field
from typing import Any, Optional, Union
from networkx import DiGraph


@dataclass
class ControlFlowGraph:
    dot: str
    graph: DiGraph | None
    node_count: int
    edge_count: int
    parse_error: Optional[str] = None


@dataclass
class CallbackThread:
    callback_name: str
    key_expr: str
    cfg: ControlFlowGraph


# TODO change CFG schemas
@dataclass
class MainThread:
    cfg: ControlFlowGraph

@dataclass
class ExecutionBranch:
    node: Union[MainThread, CallbackThread]

    @property
    def name(self):
        if isinstance(self.node, MainThread):
            return "main"
        elif isinstance(self.node, CallbackThread):
            return self.node.callback_name
        else:
            raise ValueError("Invalid node type")


@dataclass 
class VarPublisher:
    var: str
    key_expr: str

@dataclass
class SessPublisher:
    var: str
    key_exprs: list[str]


@dataclass
class TranslationUnit:
    file_name: str
    main_thread: MainThread
    callback_threads: list[CallbackThread] = field(default_factory=list)
    var_publishers: list[VarPublisher] = field(default_factory=list)
    sess_publishers: list[SessPublisher] = field(default_factory=list)