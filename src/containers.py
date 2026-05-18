from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class PutStmt:
    keyExpr: str
    controlFlow: list = field(default_factory=list)

@dataclass
class Subscriber:
    keyExpr: str
    callback: str
    putStmts: list[PutStmt] = field(default_factory=list)
    
@dataclass
class Publisher:
    keyExpr: str

@dataclass
class Unit:
    filename: str
    subscribers: list[Subscriber] = field(default_factory=list)
    publishers: list[Publisher] = field(default_factory=list)


@dataclass
class ControlFlowGraph:
    dot: str
    graph: Optional[Any]
    node_count: int
    edge_count: int
    parse_error: Optional[str] = None


@dataclass
class CallbackNode:
    file_name: str
    callback: str
    key_expr: str
    cfg: ControlFlowGraph
    callback_full_name: Optional[str] = None


@dataclass
class MainCFG:
    file_name: str
    cfg: ControlFlowGraph
    main_full_name: Optional[str] = None


@dataclass
class TranslationUnit:
    main_cfg: MainCFG
    callback_cfgs: list[CallbackNode] = field(default_factory=list)
    called_method_fullnames: list[str] = field(default_factory=list)