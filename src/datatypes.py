from dataclasses import dataclass, field
from typing import Any, Optional


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
class VarPublisher:
    var: str
    key_expr: str

@dataclass
class SessPublisher:
    var: str
    key_exprs: list[str]


@dataclass
class TranslationUnit:
    main_cfg: MainCFG
    callback_cfgs: list[CallbackNode] = field(default_factory=list)
    var_publishers: list[VarPublisher] = field(default_factory=list)
    sess_publishers: list[SessPublisher] = field(default_factory=list)
    called_method_fullnames: list[str] = field(default_factory=list)

@dataclass
class DezyneInterface:
    name: str
    in_events: list[str] = field(default_factory=list)
    out_events: list[str] = field(default_factory=list)
    behavior: str

@dataclass
class DezyneComponent:
    name: str
    provides: Optional[str] = None
    requires: Optional[str] = None
    behavior: Optional[str] = None

@dataclass
class DezyneFile:
    filename: str
    interface: DezyneInterface
    component: DezyneComponent