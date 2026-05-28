"""Top-level Dezyne code generator: stitches together the per-unit interfaces,
the stepper, the network element, and the top model."""
import logging
import os

from ..builders import InterconnectionGraph
from ..datatypes import StateMachine, State, OutEvent, DeferTo, ChangeStateTo, TranslationUnit

from .ast import (
    ASTNode, TypeDecl, EventDecl, VarDecl, Assignment, Action, Block,
    Guard, Trigger, Behavior, Interface, Provides, Component, File,
)
from ._behavior import _generate_behavior
from ._structural import _generate_stepper, _generate_network_elt, _generate_top_model
from ._naming import mangle_topic, unit_name_from_file


logger = logging.getLogger(__name__)


def _state_var(thread: str) -> str:
    return f"s_{thread}"


def _state_type(thread: str) -> str:
    return f"State_{thread}"


def _render_state_for_thread(thread: str, state: State) -> list[Guard]:
    """Translate one mid-IR ``State`` into a list of Dezyne ``Guard`` nodes.

    Dispatch policy (the semantic core of the generator):

    - ``OutEvent(topic)``     -> ``Action(mangle_topic(topic))``
    - ``DeferTo(target)``     -> if ``target == thread``: skip (we're already on
                                  that thread); else assign the thread var and
                                  reset our own state variable to 1 so the next
                                  entry restarts the thread.
    - ``ChangeStateTo(next)`` -> handled by appending ``s_<thread> = next`` to
                                  each guard's body. Multiple successors become
                                  multiple sibling guards (nondeterministic).
    """
    inline_stmts: list[ASTNode] = []
    parks = False
    for stmt in state.statements:
        if isinstance(stmt, OutEvent):
            inline_stmts.append(Action(mangle_topic(stmt.key_expr)))
        elif isinstance(stmt, DeferTo):
            if stmt.target_execution == thread:
                continue
            inline_stmts.append(Assignment("thread", stmt.target_execution))
            inline_stmts.append(Assignment(_state_var(thread), "1"))
            parks = True
        else:
            raise TypeError(f"Unknown mid-IR statement: {type(stmt).__name__}")

    cond = f"{_state_var(thread)} == {state.value}"

    def _body(stmts: list[ASTNode]) -> ASTNode:
        if not stmts:
            return Block([])
        if len(stmts) == 1:
            return stmts[0]
        return Block(stmts)

    if not state.state_changes or parks:
        return [Guard(cond, _body(inline_stmts))]

    guards: list[Guard] = []
    for change in state.state_changes:
        with_transition = inline_stmts + [Assignment(_state_var(thread), str(change.target_state))]
        guards.append(Guard(cond, _body(with_transition)))
    return guards


def state_machines_to_code(unit_name: str, state_machines: dict[str, StateMachine]) -> tuple[str, File]:
    """Convert per-thread state machines into a single Dezyne File for one translation unit.

    Returns ``(unit_name, file)`` where the file contains an ``interface I<unit_name>``
    holding all threads dispatched by a ``CurrentExecutionThread`` enum, plus a thin
    wrapper ``component C<unit_name>`` that ``provides`` that interface.
    """
    threads = list(state_machines.keys())
    if "main" in threads:
        threads = ["main"] + [t for t in threads if t != "main"]

    out_topics: list[str] = []
    seen: set[str] = set()
    for sm in state_machines.values():
        for st in sm.states:
            for s in st.statements:
                if isinstance(s, OutEvent):
                    m = mangle_topic(s.key_expr)
                    if m not in seen:
                        seen.add(m)
                        out_topics.append(m)

    events: list[EventDecl] = [EventDecl(t, "out") for t in out_topics]
    events.append(EventDecl("step", "in"))

    type_decls: list[TypeDecl] = [TypeDecl("enum", "CurrentExecutionThread", threads)]
    for t in threads:
        type_decls.append(TypeDecl("subint", _state_type(t), ["1", str(max(state_machines[t].num_states, 1))]))

    var_decls: list[VarDecl] = [VarDecl("CurrentExecutionThread", "thread", "main")]
    for t in threads:
        var_decls.append(VarDecl(_state_type(t), _state_var(t), "1"))

    thread_branches: list[Guard] = []
    for t in threads:
        guards: list[Guard] = []
        for st in state_machines[t].states:
            guards.extend(_render_state_for_thread(t, st))
        thread_branches.append(Guard(f"thread == {t}", Block(guards)))

    behavior = Behavior(
        type_decls=type_decls,
        var_decls=var_decls,
        statements=[Trigger("step", Block(thread_branches))],
    )

    iface = Interface(name=f"I{unit_name}", events=events, behavior=behavior)
    comp = Component(name=f"C{unit_name}", provides=[Provides(f"I{unit_name}", f"{unit_name}_top")])
    return unit_name, File(imports=["Utils/Step.dzn"], body=[iface, comp])


class CodeGenerator:
    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        self.unit_files: dict[str, File] = {}
        self.stepper: File | None = None
        self.network: File | None = None
        self.top: File | None = None

    def generate(self, model: InterconnectionGraph, single_stepper: bool = False):
        """Generate Dezyne code from the given interconnection graph.

        Populates ``self.unit_files``, ``self.stepper``, ``self.network`` and
        ``self.top``. Call :meth:`printToOutput` to flush them to disk.
        """
        unit_files: dict[str, File] = {}
        unit_by_id: dict[int, str] = {}

        for node_id, attrs in model:
            tu: TranslationUnit = attrs["data"]
            name = unit_name_from_file(tu.file_name)
            state_machines = _generate_behavior(tu)
            unit_name, file = state_machines_to_code(name, state_machines)
            unit_files[unit_name] = file
            unit_by_id[node_id] = unit_name

        self.unit_files = unit_files
        self.stepper = _generate_stepper()
        self.network = _generate_network_elt(model, unit_by_id, single_stepper=single_stepper)
        self.top = _generate_top_model(model, unit_by_id, single_stepper=single_stepper)
        return unit_files, self.stepper, self.network, self.top

    def printToOutput(self):
        """Flush every generated File to ``self.output_dir``."""
        os.makedirs(self.output_dir, exist_ok=True)
        utils_dir = os.path.join(self.output_dir, "Utils")
        os.makedirs(utils_dir, exist_ok=True)

        for name, file in self.unit_files.items():
            path = os.path.join(self.output_dir, f"{name}.dzn")
            with open(path, "w") as fp:
                fp.write(file.to_code())
            logger.info("Wrote %s", path)

        if self.stepper is not None:
            path = os.path.join(utils_dir, "Step.dzn")
            with open(path, "w") as fp:
                fp.write(self.stepper.to_code())
            logger.info("Wrote %s", path)

        if self.network is not None:
            path = os.path.join(self.output_dir, "Network.dzn")
            with open(path, "w") as fp:
                fp.write(self.network.to_code())
            logger.info("Wrote %s", path)

        if self.top is not None:
            path = os.path.join(self.output_dir, "Top.dzn")
            with open(path, "w") as fp:
                fp.write(self.top.to_code())
            logger.info("Wrote %s", path)
