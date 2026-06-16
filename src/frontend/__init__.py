"""Joern code analysis frontend.

``JoernClient`` is the generic Joern access layer; middleware-specific
extraction lives in :mod:`src.frontend.extractors`.

Example:
    >>> from src.frontend import JoernClient, get_extractor
    >>> with JoernClient("http://localhost:8080") as client:
    ...     client.open_project("my-project")
    ...     pubs = get_extractor("zenoh").extract_publishers(client, "A.cpp")
"""

from .client import JoernClient
from .extractors import MiddlewareExtractor, get_extractor, EXTRACTORS

__all__ = ["JoernClient", "MiddlewareExtractor", "get_extractor", "EXTRACTORS"]
