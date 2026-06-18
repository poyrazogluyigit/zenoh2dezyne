"""Generic Joern access — middleware-agnostic.

JoernClient owns the connection lifecycle, project lifecycle, and the generic
CPG queries (files, CFGs). Middleware-specific extraction (publishers,
subscribers, services) lives in :mod:`src.frontend.extractors`, which compose
on top of :meth:`JoernClient.run_query`.
"""
import logging
from functools import wraps
from typing import Any

from ._connection import Connection
from ._joern_parsers import _parse_joern_json

logger = logging.getLogger(__name__)


class JoernClient:
    """Connection + generic query surface for a running Joern server."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __init__(self, joern_server: str = ""):
        """Args:
            joern_server: URL of Joern server (e.g., "http://localhost:8080").
                          If empty, a local Joern server is started.
        """
        self._connection = Connection(joern_server)

    def _send_query(self, query: str) -> str:
        """Send a raw Joern query string and return the raw stdout."""
        return self._connection.sendQuery(query)

    def run_query(self, scala: str) -> Any:
        """Run a Joern query that returns JSON-serializable data.

        Appends ``.toJson``, sends, and parses the response. Extractors build
        their Scala query strings and call this.
        """
        return _parse_joern_json(self._send_query(scala + ".toJson"))

    @staticmethod
    def _query(func):
        """Decorator: the wrapped method returns a Scala query string; the
        decorator runs it via :meth:`run_query` and returns parsed JSON."""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return self.run_query(func(self, *args, **kwargs))
        return wrapper

    def open_project(self, project_name: str) -> str:
        """Open an existing Joern project by name.

        ``open()`` returns a ``Project`` whose ``.toJson`` reflection fails on
        Java 17+ (``UnixPath`` module access); send raw and ignore the response.
        """
        logger.debug(f"Opening Joern project: {project_name}")
        return self._send_query(f'open("{project_name}")')

    def import_code(self, input_path: str, project_name: str) -> str:
        """Import a source directory as ``project_name`` (also opens it).

        Same raw-send rationale as :meth:`open_project`.
        """
        logger.debug(f"Importing code from {input_path} as project {project_name}")
        return self._send_query(
            f'importCode(inputPath="{input_path}", projectName="{project_name}")'
        )

    def delete_project(self, project_name: str) -> str:
        """Delete a project by name for idempotent re-imports.

        Best-effort delete so re-import over an existing <out> is idempotent.
        Returns the raw query result without JSON parsing.
        """
        logger.debug(f"Deleting Joern project: {project_name}")
        return self._send_query(f'delete("{project_name}")')

    @_query
    def get_files(self):
        return 'cpg.file.name(".*\\\\.cpp").map(_.name)'

    @_query
    def get_cfg_as_dot(self, file_name: str, function_name: str):
        logger.debug(f"Retrieving CFG for {function_name} from {file_name}")
        return f'cpg.method.filename("{file_name}").name("{function_name}").dotCfg'

    def close(self) -> None:
        logger.debug("Closing Joern connection")
        self._connection.stop()
