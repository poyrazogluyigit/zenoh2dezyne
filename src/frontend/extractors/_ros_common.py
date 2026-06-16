"""Shared Joern query builders for ROS1/ROS2.

Joern's fuzzy C++ frontend misparses templated calls — ``create_publisher<T>(...)``
becomes a field access plus ``<``/``>`` comparison operators, so the call does
not appear as a ``cpg.call.name("create_publisher")`` node. Extraction therefore
anchors on the enclosing assignment and recovers the topic from string literals
and the callback identifier from the assignment code. ROS1 and ROS2 share this
shape, differing only in call names (``advertise``/``create_publisher``,
``subscribe``/``create_subscription``).
"""
import re

from ...datatypes import Publisher, Subscriber
from ...graphutils import JoernCFG

_QUOTED = re.compile(r'"([^"]*)"')


def _first_quoted(literals: list[str]) -> str | None:
    return next((lit for lit in literals if lit.startswith('"')), None)


def _parse_callback(code: str) -> str | None:
    """Recover the callback identifier from a subscribe/create_subscription call.

    Handles ``&topic_callback`` (ROS2/free-function-address) and bare
    ``chatterCallback`` (ROS1). Takes the last call argument and strips a
    leading ``&``.
    """
    open_paren = code.find("(")
    close_paren = code.rfind(")")
    if open_paren == -1 or close_paren <= open_paren:
        return None
    last_arg = code[open_paren + 1:close_paren].split(",")[-1].strip().lstrip("&").strip()
    match = re.search(r"([A-Za-z_]\w*)$", last_arg)
    return match.group(1) if match else None


def extract_handle_publishers(client, file: str, call_name: str) -> list[Publisher]:
    data = client.run_query(
        f'cpg.assignment.where(_.file.name("{file}"))'
        f'.where(_.code(".*{call_name}.*"))'
        f'.map {{ a => (a.target.code, a.ast.isLiteral.code.l) }}'
    )
    publishers: list[Publisher] = []
    for item in data:
        for handle, literals in item.items():
            topic = _first_quoted(literals)
            if topic is not None:
                publishers.append(Publisher(symbol=handle, topic=topic))
    return publishers


def extract_callback_subscribers(client, file: str, call_name: str) -> list[Subscriber]:
    codes = client.run_query(
        f'cpg.assignment.where(_.file.name("{file}"))'
        f'.where(_.code(".*{call_name}.*")).code.dedup.l'
    )
    subscribers: list[Subscriber] = []
    for code in codes:
        topic_match = _QUOTED.search(code)
        cb_name = _parse_callback(code)
        if topic_match is None or cb_name is None:
            continue
        cfgs = client.run_query(f'cpg.method.name("{cb_name}").dotCfg.l')
        if not cfgs:
            continue
        subscribers.append(
            Subscriber(name=cb_name, topic=f'"{topic_match.group(1)}"', cfg=JoernCFG(cfgs[0]))
        )
    return subscribers
