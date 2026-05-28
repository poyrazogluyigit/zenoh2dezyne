from dataclasses import dataclass

class ASTNode:
    def to_code(self) -> str:
        '''Convert this AST node to Dezyne code.'''
        raise NotImplementedError("to_code method not implemented for ASTNode")
    
@dataclass
class TypeDecl(ASTNode):
    type_kind: str
    name: str
    values: list[str] | None = None

    def to_code(self) -> str:
        if self.type_kind == 'enum':
            values_str = ", ".join(self.values) if self.values else ""
            return f"enum {self.name} {{ {values_str} }}"
        elif self.type_kind == 'subint':
            return f"subint {self.name} {{ 1..{self.values[0]} }}"
        
@dataclass
class Event(ASTNode):
    name: str
    direction: str

    def to_action_code(self) -> str:
        return self.name
    
    def to_decl_code(self) -> str:
        return f"{self.direction} {self.name}();"
    
@dataclass
class EventDecl(Event):
    def to_code(self) -> str:
        return self.to_decl_code()

@dataclass
class Block(ASTNode):
    statements: list[ASTNode]

    def to_code(self) -> str:
        return "{\n" + "\n".join(stmt.to_code() for stmt in self.statements) + "\n}"
    
@dataclass
class Variable(ASTNode):
    name: str

    def to_code(self) -> str:
        return self.name
    
