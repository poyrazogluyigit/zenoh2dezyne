from dataclasses import dataclass, field
from graphutils import JoernCFG


@dataclass
class CallbackThread:
    cfg: JoernCFG
    name: str
    key_expr: str


@dataclass
class MainThread:
    cfg: JoernCFG
    _name: str = "main"

    @property
    def name(self):
        return self._name

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
    main: MainThread
    callbacks: list[CallbackThread] = field(default_factory=list)
    var_publishers: list[VarPublisher] = field(default_factory=list)
    sess_publishers: list[SessPublisher] = field(default_factory=list)