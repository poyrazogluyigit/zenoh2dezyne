"""Structural generators: the Stepper, the Network element, and the Top model.

These consume the :class:`InterconnectionGraph` (and per-unit interface
information) and produce Dezyne AST :class:`File` nodes directly.
"""
from .ast import (
    Action,
    ASTNode,
    Behavior,
    Binding,
    Block,
    Component,
    EventDecl,
    File,
    Instance,
    Interface,
    Provides,
    Requires,
    System,
    Trigger,
)
from ._naming import mangle_topic
from ..builders import InterconnectionGraph


def _generate_stepper() -> File:
    """Produce the canonical ``Utils/Step.dzn`` file."""
    iface = Interface(
        name="IStep",
        events=[EventDecl("step", "out")],
        behavior=Behavior(statements=[Trigger("inevitable", Action("step"))]),
    )
    comp = Component(name="Step", provides=[Provides("IStep", "step")])
    return File(body=[iface, comp])


def _generate_network_elt(
    model: InterconnectionGraph,
    unit_by_id: dict[int, str],
    unit_signals: dict[str, list[str]] | None = None,
    unit_out_topics: dict[str, list[str]] | None = None,
) -> File:
    """Produce ``Network.dzn``: an ``INetCtl`` interface and a ``Network`` component
    that routes every published topic to its subscribing units and dispatches
    per-unit (or shared) step events.

    Dezyne requires every output of a ``requires`` interface to be addressed.
    This function therefore enumerates three categories per unit and emits a
    trigger for each:

    1. **Routed topics** — IG edges from this unit to one or more subscribers.
       Multiple subscribers on the same (src, topic) produce a single trigger
       whose body fires each destination sequentially.
    2. **Orphan topics** (``unit_out_topics`` minus routed) — declared by the
       interface but with no subscriber in the IG. Empty ``{}`` handler.
    3. **Branch-signal events** (``unit_signals``) — verifier observation
       events from nondeterministic transitions. Always empty handler.
    """
    units = [unit_by_id[i] for i in sorted(unit_by_id.keys())]
    unit_signals = unit_signals or {}
    unit_out_topics = unit_out_topics or {}

    imports = [f"{u}.dzn" for u in units] + ["Step.dzn"]

    netctl_iface = Interface(
        name="INetCtl",
        events=[EventDecl("kick", "in")],
        behavior=Behavior(statements=[Trigger("kick", Block([]))]),
    )

    provides = [Provides("INetCtl", "ctl")]
    requires = [Requires(f"I{u}", u) for u in units]

    for i, _ in enumerate(units, start=1):
        requires.append(Requires("IStep", f"s{i}"))

    bhv_statements: list = [Trigger("ctl.kick()", Block([]))]

    # Group edges by (src_unit, mangled_topic) so multiple subscribers on the
    # same publication fan out into a single trigger with a sequential body.
    edges_by_src: dict[tuple[str, str], list[str]] = {}
    for src, dst, topic in model.graph.edges(keys=True):
        key = (unit_by_id[src], mangle_topic(topic))
        edges_by_src.setdefault(key, []).append(unit_by_id[dst])

    routed: set[tuple[str, str]] = set()
    for (src_unit, m), dst_units in edges_by_src.items():
        routed.add((src_unit, m))
        if len(dst_units) == 1:
            body: ASTNode = Action(f"{dst_units[0]}.{m}()")
        else:
            body = Block([Action(f"{d}.{m}()") for d in dst_units])
        bhv_statements.append(Trigger(f"{src_unit}.{m}()", body))

    # Orphan-publisher empty handlers: every declared out-topic without a
    # routing trigger needs an empty handler so Dezyne is satisfied.
    for u in units:
        for topic in unit_out_topics.get(u, []):
            if (u, topic) not in routed:
                bhv_statements.append(Trigger(f"{u}.{topic}()", Block([])))

    # Empty handlers for every branch-signal out event of every required unit.
    for u in units:
        for sig in unit_signals.get(u, []):
            bhv_statements.append(Trigger(f"{u}.{sig}()", Block([])))

    for i, u in enumerate(units, start=1):
        bhv_statements.append(Trigger(f"s{i}.step()", Action(f"{u}.step()")))

    net_comp = Component(
        name="Network",
        provides=provides,
        requires=requires,
        behavior=Behavior(statements=bhv_statements),
    )

    return File(imports=imports, body=[netctl_iface, net_comp])


def _generate_top_model(
    model: InterconnectionGraph,
    unit_by_id: dict[int, str],
) -> File:
    """Produce ``Top.dzn``: a system block that instantiates the Network, the
    units' components, and the steppers, plus the bindings between them."""
    units = [unit_by_id[i] for i in sorted(unit_by_id.keys())]

    imports = [f"{u}.dzn" for u in units] + ["Step.dzn", "Network.dzn"]

    instances: list[Instance] = [Instance("Network", "net")]
    instances.extend(Instance(f"C{u}", f"{u}_comp") for u in units)

    bindings: list[Binding] = [Binding("net_ctl", "net.ctl")]
    bindings.extend(Binding(f"{u}_comp.{u}_top", f"net.{u}") for u in units)

    for i, _ in enumerate(units, start=1):
        instances.append(Instance("Step", f"s{i}"))
        bindings.append(Binding(f"net.s{i}", f"s{i}.step"))

    top_comp = Component(
        name="Top",
        provides=[Provides("INetCtl", "net_ctl")],
        system=System(instances=instances, bindings=bindings),
    )
    return File(imports=imports, body=[top_comp])
