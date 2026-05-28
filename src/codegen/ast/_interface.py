from dataclasses import dataclass
from .ast import ASTNode, Block, EventDecl, Variable, TypeDecl, Event

@dataclass
class Guard(ASTNode):
    condition: str
    rhs: Block

    def to_code(self) -> str:
        return f"[{self.condition}] {self.rhs.to_code()}"


@dataclass
class Trigger(ASTNode):
    event: str

    def to_code(self) -> str:
        return f"on {self.event}:"
    
@dataclass
class Action(Event):
    def to_code(self) -> str:
        return self.to_action_code()

    
@dataclass
class Assignment(ASTNode):
    variable: Variable
    value: str

    def to_code(self) -> str:
        return f"{self.variable} = {self.value};"
    
@dataclass
class VarDecl(ASTNode):
    variable: Variable
    initial_value: str

    def to_code(self) -> str:
        return f"var {self.variable} = {self.initial_value};"
    
@dataclass
class Behavior:
    var_decls: list[VarDecl]
    statements = list[Guard | Trigger]

    def to_code(self) -> str:
        var_decls_code = "\n".join(var.to_code() for var in self.var_decls)
        statements_code = "\n".join(stmt.to_code() for stmt in self.statements)
        return f"behavior {{\n{var_decls_code}\n{statements_code}\n}}"

@dataclass 
class Interface:
    type_decls: list[TypeDecl]
    events: list[EventDecl]
    behavior: Behavior
