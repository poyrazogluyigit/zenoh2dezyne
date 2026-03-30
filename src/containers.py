from dataclasses import dataclass, field

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