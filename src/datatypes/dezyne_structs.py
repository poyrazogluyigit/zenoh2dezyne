from dataclasses import dataclass, field

@dataclass
class DezyneStateVar:
    name: str
    lower_bound: int = 1
    upper_bound: int = 2
    
    @property 
    def initial_value(self):
        return self.lower_bound

@dataclass
class DezyneGuard:
    variable: str
    value: int

@dataclass
class DezyneTrigger:
    trigger: str

@dataclass
class DezyneVarSet:
    variable: str
    value: str

@dataclass
class DezyneAction:
    out_event: str

@dataclass
class DezyneBehaviorStatement:
    lhs: DezyneGuard | DezyneTrigger
    rhs: list[str] = field(default_factory=list)

@dataclass
class DezyneEnumDecl:
    name: str
    values: list[str] = field(default_factory=list)

@dataclass
class DezyneEnumVariableDecl:
    name: str
    enum_type: str
    value: str

@dataclass
class DezyneBehavior:
    state_vars: list[DezyneStateVar] = field(default_factory=list)
    statements: list[DezyneBehaviorStatement] = field(default_factory=list)

    @property
    def possible_executions(self):
        return ["main"] + [state_var.name for state_var in self.state_vars]



@dataclass
class DezyneInterface:
    name: str
    behavior: DezyneBehavior
    in_events: list[str] = field(default_factory=list)
    out_events: list[str] = field(default_factory=list)

@dataclass
class DezyneComponent:
    name: str
    provides: list[DezyneInterface] = field(default_factory=list)
    requires: list[DezyneInterface] = field(default_factory=list)
    behavior: str | None = None

@dataclass
class DezyneFile:
    file_name: str
    interface: DezyneInterface
    component: DezyneComponent