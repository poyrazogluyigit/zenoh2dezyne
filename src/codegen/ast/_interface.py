"""Interface, Behavior, Guard, Trigger AST nodes."""
from dataclasses import dataclass, field
from .ast import ASTNode, Block, EventDecl, TypeDecl, VarDecl, _indent


@dataclass
class Guard(ASTNode):
    """A guard clause: ``[condition] <rhs>``.

    ``rhs`` may be any statement (e.g. ``Assignment``, ``Action``) or a ``Block``.
    """
    condition: str
    rhs: ASTNode

    def to_code(self) -> str:
        return f"[{self.condition}] {self.rhs.to_code()}"


@dataclass
class Trigger(ASTNode):
    """An ``on <event>: <body>`` clause.

    ``event`` may be a bare name (``step``), a qualified port event (``A.basic_B_A()``),
    or a special keyword like ``inevitable``. ``body`` may be a ``Block`` or a single
    statement.
    """
    event: str
    body: ASTNode

    def to_code(self) -> str:
        return f"on {self.event}: {self.body.to_code()}"


@dataclass
class Behavior(ASTNode):
    """A ``behavior { ... }`` block: type declarations, variable declarations, and triggers/guards."""
    type_decls: list[TypeDecl] = field(default_factory=list)
    var_decls: list[VarDecl] = field(default_factory=list)
    statements: list[ASTNode] = field(default_factory=list)

    def to_code(self) -> str:
        parts: list[str] = []
        if self.type_decls:
            parts.extend(t.to_code() for t in self.type_decls)
        if self.var_decls:
            parts.extend(v.to_code() for v in self.var_decls)
        if self.statements:
            parts.extend(s.to_code() for s in self.statements)
        if not parts:
            return "behavior {}"
        body = "\n".join(parts)
        return "behavior {\n" + _indent(body) + "\n}"


@dataclass
class Interface(ASTNode):
    """A Dezyne interface: ``interface IName { <type decls> <event decls> behavior { ... } }``."""
    name: str
    type_decls: list[TypeDecl] = field(default_factory=list)
    events: list[EventDecl] = field(default_factory=list)
    behavior: Behavior | None = None

    def to_code(self) -> str:
        parts: list[str] = []
        if self.type_decls:
            parts.extend(t.to_code() for t in self.type_decls)
        if self.events:
            parts.extend(e.to_code() for e in self.events)
        if self.behavior is not None:
            parts.append(self.behavior.to_code())
        body = "\n".join(parts) if parts else ""
        if not body:
            return f"interface {self.name} {{}}"
        return f"interface {self.name} {{\n" + _indent(body) + "\n}"
