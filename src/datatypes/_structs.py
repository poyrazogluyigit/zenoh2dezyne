from dataclasses import dataclass, field

@dataclass
class OutEvent:
    key_expr: str

@dataclass
class DeferTo:
    target_execution: str

@dataclass
class ChangeStateTo:
    target_state: int

@dataclass
class State:
    value: int
    statements: list[str] = field(default_factory=list)

# TODO force ordering of states by increasing state number, also add iterator
@dataclass
class StateMachine:
    states: list[State] = field(default_factory=list)

    @property
    def num_states(self):
        return len(self.states)
    
