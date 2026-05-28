"""Component / System / Provides / Requires / Binding AST nodes."""
from dataclasses import dataclass, field
from .ast import ASTNode, _indent
from ._interface import Behavior


@dataclass
class Provides(ASTNode):
    """``provides <interface_type> <port_name>;``"""
    interface_type: str
    port_name: str

    def to_code(self) -> str:
        return f"provides {self.interface_type} {self.port_name};"


@dataclass
class Requires(ASTNode):
    """``requires <interface_type> <port_name>;``"""
    interface_type: str
    port_name: str

    def to_code(self) -> str:
        return f"requires {self.interface_type} {self.port_name};"


@dataclass
class Instance(ASTNode):
    """A component instance inside a ``system`` block: ``<TypeName> <name>;``."""
    type_name: str
    name: str

    def to_code(self) -> str:
        return f"{self.type_name} {self.name};"


@dataclass
class Binding(ASTNode):
    """A port binding inside a ``system`` block: ``lhs <=> rhs;``."""
    lhs: str
    rhs: str

    def to_code(self) -> str:
        return f"{self.lhs} <=> {self.rhs};"


@dataclass
class System(ASTNode):
    """A ``system { ... }`` block: instances followed by bindings."""
    instances: list[Instance] = field(default_factory=list)
    bindings: list[Binding] = field(default_factory=list)

    def to_code(self) -> str:
        parts: list[str] = [i.to_code() for i in self.instances]
        if self.instances and self.bindings:
            parts.append("")  # blank line between instances and bindings
        parts.extend(b.to_code() for b in self.bindings)
        if not parts:
            return "system {}"
        body = "\n".join(parts)
        return "system {\n" + _indent(body) + "\n}"


@dataclass
class Component(ASTNode):
    """A Dezyne component. Has ``provides``/``requires`` ports and either a ``behavior`` or a ``system`` block."""
    name: str
    provides: list[Provides] = field(default_factory=list)
    requires: list[Requires] = field(default_factory=list)
    behavior: Behavior | None = None
    system: System | None = None

    def to_code(self) -> str:
        parts: list[str] = []
        parts.extend(p.to_code() for p in self.provides)
        parts.extend(r.to_code() for r in self.requires)
        if self.behavior is not None:
            if parts:
                parts.append("")
            parts.append(self.behavior.to_code())
        if self.system is not None:
            if parts:
                parts.append("")
            parts.append(self.system.to_code())
        body = "\n".join(parts) if parts else ""
        if not body:
            return f"component {self.name} {{}}"
        return f"component {self.name} {{\n" + _indent(body) + "\n}"
