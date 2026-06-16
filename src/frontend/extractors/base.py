"""Middleware extractor seam.

A ``MiddlewareExtractor`` knows how one pub/sub framework appears in the Joern
CPG and how its publish calls resolve to topics. All middleware knowledge lives
behind this Protocol; the builders and codegen stay framework-agnostic.
"""
from typing import Protocol, runtime_checkable

from ...datatypes import Publisher, Subscriber


@runtime_checkable
class MiddlewareExtractor(Protocol):
    name: str
    publish_call_names: frozenset[str]

    def extract_publishers(self, client, file: str) -> list[Publisher]: ...
    def extract_subscribers(self, client, file: str) -> list[Subscriber]: ...
    def resolve_publish_topic(self, node_code: str, publishers: list[Publisher]) -> str | None: ...


class BaseExtractor:
    """Common default for publish-topic resolution.

    Concrete extractors inherit this to pick up the handle-based default; new
    optional primitives can land here as defaulted methods later.
    """
    name: str = ""
    publish_call_names: frozenset[str] = frozenset()

    # FIXME pointer/variable thing may happen on both zenoh and ros; investigate
    def resolve_publish_topic(self, node_code: str, publishers: list[Publisher]) -> str | None:
        """Default: the publish receiver is a handle created with the topic.

        Handles ``handle.publish(...)`` and ``handle->publish(...)`` (ROS uses
        the arrow form on pointer handles). Frameworks with non-handle publish
        forms (e.g. Zenoh's ``session.put(literal, ...)``) override this.
        """
        receiver = node_code.replace("->", ".").split(".")[0].strip()
        match = next((p for p in publishers if p.symbol == receiver), None)
        return match.topic if match else None
