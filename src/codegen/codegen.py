"""Top-level Dezyne code generator: stitches together the per-unit interfaces,
the network element, and the top model."""
import logging
import os
from dataclasses import dataclass, field

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


_THREAD_ENUM = "CurrentExecutionThread"


def _state_var(thread: str) -> str:
    return f"s_{thread}"


def _state_type(thread: str) -> str:
    return f"State_{thread}"


@dataclass
class UnitCodegenResult:
    """The artefacts produced for one translation unit.

    Carries everything Network needs to address the unit: the file itself, its
    out-topics (need either routing edges or empty handlers in Network), its
    branch-signal out-events (always empty handlers), and its in-topics (used
    to detect orphan subscriptions).
    """
    name: str
    file: "File"
    out_topics: list[str] = field(default_factory=list)
    signal_events: list[str] = field(default_factory=list)
    in_topics: list[str] = field(default_factory=list)


def _thread_value(thread: str) -> str:
    """Dezyne-qualified enum value, e.g. ``CurrentExecutionThread.main``.

    Bare identifiers (just ``main``) would be parsed as variable references, so
    enum values must be qualified by the enum type in every position — guards,
    assignments, and initializers.
    """
    return f"{_THREAD_ENUM}.{thread}"


def _branch_signal(thread: str, source: int, target: int) -> str:
    """Name of the out-event fired when ``thread`` transitions from ``source`` to ``target``.

    For nondeterministic states (multiple successors) the verifier needs a way
    to observe which branch was taken; we emit one of these out-events before
    the state assignment in each guard's body.
    """
    return f"{thread}_branch_{source}_to_{target}"


def _render_state_for_thread(thread: str, state: State) -> tuple[list[Guard], list[str]]:
    """Translate one mid-IR ``State`` into Dezyne ``Guard`` nodes plus the
    branch-signal event names that those guards fire.

    Dispatch policy (the semantic core of the generator):

    - ``OutEvent(topic)``     -> ``Action(mangle_topic(topic))``
    - ``DeferTo(target)``     -> if ``target == thread``: skip (we're already on
                                  that thread); else assign the thread var and
                                  reset our own state variable to 1 so the next
                                  entry restarts the thread.
    - ``ChangeStateTo(next)`` -> handled by appending ``s_<thread> = next`` to
                                  each guard's body. Multiple successors become
                                  multiple sibling guards (nondeterministic);
                                  each branch also fires an out-event signal so
                                  the verifier can observe which one was taken.
    """
    inline_stmts: list[ASTNode] = []
    parks = False
    for stmt in state.statements:
        if isinstance(stmt, OutEvent):
            inline_stmts.append(Action(mangle_topic(stmt.key_expr)))
        elif isinstance(stmt, DeferTo):
            if stmt.target_execution == thread:
                continue
            inline_stmts.append(Assignment("thread", _thread_value(stmt.target_execution)))
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
        return [Guard(cond, _body(inline_stmts))], []

    multi = len(state.state_changes) > 1
    guards: list[Guard] = []
    signals: list[str] = []
    for change in state.state_changes:
        branch_stmts = list(inline_stmts)
        if multi:
            sig = _branch_signal(thread, state.value, change.target_state)
            signals.append(sig)
            branch_stmts.append(Action(sig))
        branch_stmts.append(Assignment(_state_var(thread), str(change.target_state)))
        guards.append(Guard(cond, _body(branch_stmts)))
    return guards, signals


def state_machines_to_code(
    unit_name: str,
    state_machines: dict[str, StateMachine],
    callback_topics: dict[str, list[str]] | None = None,
    declared_topics: list[str] | None = None,
) -> UnitCodegenResult:
    """Convert per-thread state machines into a single Dezyne File for one translation unit.

    Returns ``(unit_name, file, signal_events)`` where the file contains an
    ``interface I<unit_name>`` holding all threads dispatched by a
    ``CurrentExecutionThread`` enum, plus a thin wrapper ``component C<unit_name>``
    that ``provides`` that interface. ``signal_events`` is the list of branch-signal
    out-event names declared by the interface — required so callers (e.g. the
    Network generator) can stub empty handlers for each one.

    ``callback_topics`` maps each callback thread name to the **list** of Zenoh
    key expressions that invoke it (a single callback function may be wired to
    several ``declare_subscriber`` calls). For each topic we declare an
    ``in void <mangled>()`` event and a trigger that, when fired on main,
    switches execution into the callback (resetting its state variable to 1).

    ``declared_topics`` is the unit's complete publishing surface (all
    ``declare_publisher`` topics and any ``session.put`` topics) — including
    topics that are never actually fired in any state machine. Listing them
    ensures the interface advertises the same topics the IG considers
    outgoing, so Network's routing triggers always match an existing event.
    """
    callback_topics = callback_topics or {}
    declared_topics = declared_topics or []

    threads = list(state_machines.keys())
    if "main" in threads:
        threads = ["main"] + [t for t in threads if t != "main"]

    # Pass 1: collect out events (mangled topics).
    # Source 1 — topics actually `.put()`'d in some state machine.
    # Source 2 — topics declared via `declare_publisher` or `session.put` even
    #            if never fired. These must still be advertised so the IG's
    #            routing edges into this unit reference a known event.
    out_topics: list[str] = []
    seen_topics: set[str] = set()
    for sm in state_machines.values():
        for st in sm.states:
            for s in st.statements:
                if isinstance(s, OutEvent):
                    m = mangle_topic(s.key_expr)
                    if m not in seen_topics:
                        seen_topics.add(m)
                        out_topics.append(m)
    for t in declared_topics:
        m = mangle_topic(t)
        if m not in seen_topics:
            seen_topics.add(m)
            out_topics.append(m)

    # Pass 2: render guards and collect the branch-signal names they introduce.
    per_thread_guards: dict[str, list[Guard]] = {}
    signal_events: list[str] = []
    seen_signals: set[str] = set()
    for t in threads:
        guards: list[Guard] = []
        for st in state_machines[t].states:
            state_guards, state_signals = _render_state_for_thread(t, st)
            guards.extend(state_guards)
            for sig in state_signals:
                if sig not in seen_signals:
                    seen_signals.add(sig)
                    signal_events.append(sig)
        per_thread_guards[t] = guards

    # In-events: one per (callback_thread, subscribed_topic) pair. A single
    # callback function can be wired to multiple topics — each yields its own
    # in-event and its own trigger, all switching execution into the same thread.
    in_topics: list[tuple[str, str]] = []  # (thread_name, mangled_topic)
    seen_in: set[str] = set()
    for cb_thread, key_exprs in callback_topics.items():
        for key_expr in key_exprs:
            m = mangle_topic(key_expr)
            if m in seen_in:
                continue
            seen_in.add(m)
            in_topics.append((cb_thread, m))

    # Event declarations: outs (topics), outs (branch signals), ins (subscribed topics), in step.
    events: list[EventDecl] = []
    events.extend(EventDecl(t, "out") for t in out_topics)
    events.extend(EventDecl(s, "out") for s in signal_events)
    events.extend(EventDecl(m, "in") for _, m in in_topics)
    events.append(EventDecl("step", "in"))

    # Type and var decls.
    type_decls: list[TypeDecl] = [TypeDecl("enum", "CurrentExecutionThread", threads)]
    for t in threads:
        type_decls.append(TypeDecl("subint", _state_type(t), ["1", str(max(state_machines[t].num_states, 1))]))

    var_decls: list[VarDecl] = [VarDecl(_THREAD_ENUM, "thread", _thread_value("main"))]
    for t in threads:
        var_decls.append(VarDecl(_state_type(t), _state_var(t), "1"))

    # on step: { [thread == CurrentExecutionThread.X] { ... } ... }
    thread_branches: list[Guard] = [
        Guard(f"thread == {_thread_value(t)}", Block(per_thread_guards[t])) for t in threads
    ]
    statements: list[ASTNode] = [Trigger("step", Block(thread_branches))]

    # Per-callback on-topic triggers: switch to callback on main, otherwise ignore.
    for cb_thread, mtopic in in_topics:
        statements.append(Trigger(mtopic, Block([
            Guard(f"thread == {_thread_value('main')}", Block([
                Assignment("thread", _thread_value(cb_thread)),
                Assignment(_state_var(cb_thread), "1"),
            ])),
            Guard("otherwise", Block([])),
        ])))

    behavior = Behavior(
        type_decls=type_decls,
        var_decls=var_decls,
        statements=statements,
    )

    iface = Interface(name=f"I{unit_name}", events=events, behavior=behavior)
    comp = Component(name=f"C{unit_name}", provides=[Provides(f"I{unit_name}", f"{unit_name}_top")])
    return UnitCodegenResult(
        name=unit_name,
        file=File(imports=["Step.dzn"], body=[iface, comp]),
        out_topics=out_topics,
        signal_events=signal_events,
        in_topics=[m for _, m in in_topics],
    )


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
        unit_signals: dict[str, list[str]] = {}
        unit_out_topics: dict[str, list[str]] = {}
        unit_in_topics: dict[str, list[str]] = {}

        for node_id, attrs in model:
            tu: TranslationUnit = attrs["data"]
            name = unit_name_from_file(tu.file_name)
            state_machines = _generate_behavior(tu)
            # Multiple `declare_subscriber` calls may share a callback function
            # (same closure state); aggregate their topics under one thread name.
            callback_topics: dict[str, list[str]] = {}
            for cb in tu.callback_threads:
                callback_topics.setdefault(cb.name, []).append(cb.topic)
            # The unit's complete publishing surface — every declared/used topic,
            # including those never fired in any CFG.
            declared_topics: list[str] = [p.topic for p in tu.publishers]
            result = state_machines_to_code(
                name, state_machines, callback_topics, declared_topics=declared_topics,
            )
            unit_files[result.name] = result.file
            unit_by_id[node_id] = result.name
            unit_signals[result.name] = result.signal_events
            unit_out_topics[result.name] = result.out_topics
            unit_in_topics[result.name] = result.in_topics

        # Orphan-subscriber check: any in-topic that no unit publishes is dead
        # at the Network level. Keep the declaration (it reflects the source's
        # intent), but warn so the user notices.
        all_published: set[str] = {t for tops in unit_out_topics.values() for t in tops}
        for u, ins in unit_in_topics.items():
            for t in ins:
                if t not in all_published:
                    logger.warning(
                        "Unit %s subscribes to topic %r but no unit publishes it — "
                        "the on-%s trigger will never fire.", u, t, t,
                    )

        self.unit_files = unit_files
        self.stepper = _generate_stepper()
        self.network = _generate_network_elt(
            model, unit_by_id,
            unit_signals=unit_signals,
            unit_out_topics=unit_out_topics,
            single_stepper=single_stepper,
        )
        self.top = _generate_top_model(model, unit_by_id, single_stepper=single_stepper)
        return unit_files, self.stepper, self.network, self.top

    def printToOutput(self):
        """Flush every generated File to ``self.output_dir``."""
        os.makedirs(self.output_dir, exist_ok=True)

        for name, file in self.unit_files.items():
            path = os.path.join(self.output_dir, f"{name}.dzn")
            with open(path, "w") as fp:
                fp.write(file.to_code())
            logger.info("Wrote %s", path)

        for name, file in (("Step", self.stepper), ("Network", self.network), ("Top", self.top)):
            if file is None:
                continue
            path = os.path.join(self.output_dir, f"{name}.dzn")
            with open(path, "w") as fp:
                fp.write(file.to_code())
            logger.info("Wrote %s", path)
