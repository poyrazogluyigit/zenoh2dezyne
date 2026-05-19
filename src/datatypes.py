from dataclasses import dataclass, field
from typing import Any, Optional, Union
from pydot import Dot


@dataclass
class ControlFlowGraph:
    dot: str
    graph: Union[Dot, None]
    node_count: int
    edge_count: int
    parse_error: Optional[str] = None


@dataclass
class CallbackNode:
    callback_name: str
    key_expr: str
    cfg: ControlFlowGraph


# TODO change CFG schemas
@dataclass
class MainNode:
    cfg: ControlFlowGraph

@dataclass
class ExecutionBranch:
    node: Union[MainNode, CallbackNode]

    @property
    def name(self):
        if isinstance(self.node, MainNode):
            return "main"
        elif isinstance(self.node, CallbackNode):
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
    main_node: MainNode
    callback_nodes: list[CallbackNode] = field(default_factory=list)
    var_publishers: list[VarPublisher] = field(default_factory=list)
    sess_publishers: list[SessPublisher] = field(default_factory=list)