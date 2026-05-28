"""Base AST nodes and statement/declaration-level building blocks for Dezyne code generation."""
from dataclasses import dataclass, field


class ASTNode:
    def to_code(self) -> str:
        '''Convert this AST node to Dezyne code.'''
        raise NotImplementedError(f"to_code method not implemented for {type(self).__name__}")


def _indent(text: str, levels: int = 1) -> str:
    pad = "    " * levels
    return "\n".join(pad + line if line else line for line in text.splitlines())


@dataclass
class TypeDecl(ASTNode):
    """A type declaration: ``enum Name { v1, v2 };`` or ``subint Name { lo..hi };``."""
    type_kind: str
    name: str
    values: list[str] | None = None

    def to_code(self) -> str:
        if self.type_kind == 'enum':
            values_str = ", ".join(self.values) if self.values else ""
            return f"enum {self.name} {{ {values_str} }};"
        elif self.type_kind == 'subint':
            # values stores [lo, hi] as strings/ints
            lo, hi = self.values[0], self.values[1]
            return f"subint {self.name} {{ {lo}..{hi} }};"
        else:
            raise ValueError(f"Unknown TypeDecl kind: {self.type_kind}")


@dataclass
class EventDecl(ASTNode):
    """An event declaration in an interface: ``in void step();`` or ``out void topic();``."""
    name: str
    direction: str  # "in" or "out"

    def to_code(self) -> str:
        return f"{self.direction} void {self.name}();"


@dataclass
class Variable(ASTNode):
    name: str

    def to_code(self) -> str:
        return self.name


@dataclass
class VarDecl(ASTNode):
    """A typed variable declaration: ``State s = 1;``."""
    type_name: str
    name: str
    initial_value: str

    def to_code(self) -> str:
        return f"{self.type_name} {self.name} = {self.initial_value};"


@dataclass
class Assignment(ASTNode):
    """An assignment statement: ``s = 2;``."""
    target: str
    value: str

    def to_code(self) -> str:
        return f"{self.target} = {self.value};"


@dataclass
class Action(ASTNode):
    """An action statement: ``step;`` or ``A.basic_B_A();`` or ``basic_B_A;``."""
    text: str

    def to_code(self) -> str:
        return f"{self.text};"


@dataclass
class Block(ASTNode):
    """A braced block of statements: ``{ stmt; stmt; }``."""
    statements: list[ASTNode] = field(default_factory=list)

    def to_code(self) -> str:
        if not self.statements:
            return "{}"
        body = "\n".join(stmt.to_code() for stmt in self.statements)
        return "{\n" + _indent(body) + "\n}"


@dataclass
class File(ASTNode):
    """A complete .dzn file: imports followed by top-level declarations."""
    imports: list[str] = field(default_factory=list)
    body: list[ASTNode] = field(default_factory=list)

    def to_code(self) -> str:
        parts = []
        if self.imports:
            parts.append("\n".join(f"import {imp};" for imp in self.imports))
        for node in self.body:
            parts.append(node.to_code())
        return "\n\n".join(parts) + "\n"
