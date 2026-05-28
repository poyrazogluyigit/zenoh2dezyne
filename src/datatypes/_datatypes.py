from dataclasses import dataclass, field
from ..graphutils import JoernCFG


@dataclass
class CallbackThread:
    name: str
    key_expr: str
    cfg: JoernCFG


@dataclass
class MainThread:
    cfg: JoernCFG

    @property
    def name(self):
        return "main"

@dataclass
class ExecutionBranch:
    node: MainThread | CallbackThread

    @property
    def name(self):
        return self.node.name

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