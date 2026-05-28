from dataclasses import dataclass, field
from .ast import ASTNode, Block, Event, Variable, TypeDecl
from ._interface import Interface

@dataclass
class System:
    ...

@dataclass
class Provides:
    interface: Interface
    name: str

@dataclass
class Requires:
    interface: Interface
    name: str

@dataclass
class Component:
    name: str
    provides: list[Provides] = field(default_factory=list)
    requires: list[Requires] = field(default_factory=list)

