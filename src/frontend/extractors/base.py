"""Middleware extractor seam.

A ``MiddlewareExtractor`` knows how one pub/sub framework appears in the Joern
CPG and how its publish calls resolve to topics. All middleware knowledge lives
behind this Protocol; the builders and codegen stay framework-agnostic.
"""
from typing import Protocol, runtime_checkable

from ...datatypes import Publisher, Subscriber, ServiceEndpoint


@runtime_checkable
class MiddlewareExtractor(Protocol):
    name: str
    publish_call_names: frozenset[str]

    def extract_publishers(self, client, file: str) -> list[Publisher]: ...
    def extract_subscribers(self, client, file: str) -> list[Subscriber]: ...
    def extract_services(self, client, file: str) -> list[ServiceEndpoint]: ...
    def resolve_publish_topic(self, node_code: str, publishers: list[Publisher]) -> str | None: ...


class BaseExtractor:
    """Default implementations for optional primitives.

    Concrete extractors inherit this only to pick up safe no-op defaults; new
    optional primitives (e.g. actions, liveliness) land here as defaulted
    methods so existing extractors need no changes.
    """
    name: str = ""
    publish_call_names: frozenset[str] = frozenset()

    def extract_services(self, client, file: str) -> list[ServiceEndpoint]:
        return []
