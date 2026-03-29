from dataclasses import dataclass

@dataclass
class PutStmt:
    keyExpr: str
    controlFlow: list = None

@dataclass
class Subscriber:
    keyExpr: str
    callback: str
    putStmts: list[PutStmt] = None
    
@dataclass
class Publisher:
    keyExpr: str

@dataclass
class Unit:
    filename: str
    subscribers: list[Subscriber] = None
    publishers: list[Publisher] = None