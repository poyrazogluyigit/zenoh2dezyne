"""Structural generators: the Stepper, the Network element, and the Top model.

These consume the :class:`InterconnectionGraph` (and per-unit interface
information) and produce Dezyne AST :class:`File` nodes directly.
"""
from .ast import (
    Action,
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
    single_stepper: bool = False,
) -> File:
    """Produce ``Network.dzn``: an ``INetCtl`` interface and a ``Network`` component
    that wires every published topic to its subscribing units and dispatches
    per-unit (or shared) step events."""
    units = [unit_by_id[i] for i in sorted(unit_by_id.keys())]

    imports = [f"{u}.dzn" for u in units] + ["Utils/Step.dzn"]

    netctl_iface = Interface(
        name="INetCtl",
        events=[EventDecl("kick", "in")],
        behavior=Behavior(statements=[Trigger("kick", Block([]))]),
    )

    provides = [Provides("INetCtl", "ctl")]
    requires = [Requires(f"I{u}", u) for u in units]

    if single_stepper:
        requires.append(Requires("IStep", "s"))
    else:
        for i, _ in enumerate(units, start=1):
            requires.append(Requires("IStep", f"s{i}"))

    bhv_statements: list = [Trigger("ctl.kick()", Block([]))]

    for src, dst, topic in model.graph.edges(keys=True):
        src_unit = unit_by_id[src]
        dst_unit = unit_by_id[dst]
        m = mangle_topic(topic)
        bhv_statements.append(
            Trigger(f"{src_unit}.{m}()", Action(f"{dst_unit}.{m}()"))
        )

    if single_stepper:
        bhv_statements.append(
            Trigger(
                "s.step()",
                Block([Action(f"{u}.step()") for u in units]),
            )
        )
    else:
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
    single_stepper: bool = False,
) -> File:
    """Produce ``Top.dzn``: a system block that instantiates the Network, the
    units' components, and the steppers, plus the bindings between them."""
    units = [unit_by_id[i] for i in sorted(unit_by_id.keys())]

    imports = [f"{u}.dzn" for u in units] + ["Utils/Step.dzn", "Network.dzn"]

    instances: list[Instance] = [Instance("Network", "net")]
    instances.extend(Instance(f"C{u}", f"{u}_comp") for u in units)

    bindings: list[Binding] = [Binding("net_ctl", "net.ctl")]
    bindings.extend(Binding(f"{u}_comp.{u}_top", f"net.{u}") for u in units)

    if single_stepper:
        instances.append(Instance("Step", "s"))
        bindings.append(Binding("net.s", "s.step"))
    else:
        for i, _ in enumerate(units, start=1):
            instances.append(Instance("Step", f"s{i}"))
            bindings.append(Binding(f"net.s{i}", f"s{i}.step"))

    top_comp = Component(
        name="Top",
        provides=[Provides("INetCtl", "net_ctl")],
        system=System(instances=instances, bindings=bindings),
    )
    return File(imports=imports, body=[top_comp])
