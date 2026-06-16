"""Middleware extractor registry.

Selection is a plain dict lookup; a future ``detect_middleware(client)`` can
resolve a name before deferring here.
"""
from .base import MiddlewareExtractor, BaseExtractor
from .zenoh import ZenohExtractor

EXTRACTORS: dict[str, type] = {
    "zenoh": ZenohExtractor,
}


def get_extractor(name: str) -> MiddlewareExtractor:
    try:
        return EXTRACTORS[name]()
    except KeyError:
        raise ValueError(
            f"Unknown middleware {name!r}; available: {sorted(EXTRACTORS)}"
        ) from None


__all__ = ["MiddlewareExtractor", "BaseExtractor", "ZenohExtractor", "EXTRACTORS", "get_extractor"]
