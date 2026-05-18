"""Joern code analysis query API.

Public interface for Joern code graph analysis.

Example:
    >>> from src.frontend import JoernQueryAPI
    >>> api = JoernQueryAPI("http://localhost:8080")
    >>> api.open_project("my-project")
    >>> publishers = api.get_publishers()
"""

from .api import JoernQueryAPI

__all__ = ["JoernQueryAPI"]
