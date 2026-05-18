"""Joern code analysis query API.

This module provides JoernQueryAPI, the main public interface for querying
Joern code graphs. It manages connection lifecycle and exposes high-level
query operations for extracting publisher/subscriber information and
control flow data from C++ applications using Zenoh.
"""
import logging
import json
import re
from functools import wraps

from ._connection import Connection

logger = logging.getLogger(__name__)


def parse_joern_json(response: str) -> object:
    """Parse Joern's JSON response, stripping ANSI codes and extracting JSON.
    
    Args:
        response: Raw response from Joern server
        
    Returns:
        Parsed JSON object
        
    Raises:
        ValueError: If response cannot be parsed as valid JSON
    """
    clean_resp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', response)
    rhs = clean_resp.split("=", 1)[-1].strip() if "=" in clean_resp else clean_resp.strip()

    if rhs.startswith('"""') and rhs.endswith('"""'):
        rhs = rhs[3:-3].strip()
    elif rhs.startswith('"') and rhs.endswith('"'):
        rhs = rhs[1:-1].encode("utf-8").decode("unicode_escape").strip()

    match = re.search(r'([\[\{].*[\]\}])', rhs, re.DOTALL)
    if match:
        rhs = match.group(1)

    try:
        return json.loads(rhs)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse Joern JSON: {exc}") from exc


class JoernQueryAPI:
    """Main API for Joern code graph analysis and query operations.
    
    Manages Joern server connection lifecycle and provides high-level query
    methods for extracting publisher/subscriber information and control flow
    data from C++ applications.
    
    The connection is managed internally; users don't need to manage connection
    lifecycle directly. The server starts on instantiation and stops on exit.
    
    Example:
        >>> api = JoernQueryAPI()
        >>> api.open_project("my-project")
        >>> publishers = api.get_publishers()
    """
    
    def __init__(self, joern_server: str = ""):
        """Initialize the Joern query API with a connection.
        
        Args:
            joern_server: URL of Joern server (e.g., "http://localhost:8080")
                         If empty, a local Joern server will be started.
        """
        self._connection = Connection(joern_server)

    def _send_query(self, query: str) -> str:
        """Send a raw Joern query and receive response.
        
        Internal method for sending raw queries.
        
        Args:
            query: The Joern query string to execute
            
        Returns:
            The response from Joern as a string
        """
        return self._connection.sendQuery(query)

    @staticmethod
    def _query_decorator(func):
        """Decorator for executing a raw Joern query.
        
        Decorated function should return a Joern query string.
        The decorator executes the query and returns the raw response.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            query_res = self._send_query(result + "")
            return query_res
        return wrapper
    
    @staticmethod
    def _json_query_decorator(func):
        """Decorator for executing a Joern query that returns JSON.
        
        Decorated function should return a Joern query string.
        The decorator executes the query with .toJson, parses the response,
        and returns the parsed JSON object.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            query_res = self._send_query(result + ".toJson")
            return parse_joern_json(query_res)
        return wrapper

    @_query_decorator
    def open_project(self, project_name: str):
        """Load a project by name into the Joern workspace.
        
        Args:
            project_name: Name of the project to open
            
        Returns:
            Response from Joern
        """
        logger.debug(f"Opening Joern project: {project_name}")
        return f'open("{project_name}")'
    
    @_json_query_decorator
    def get_publishers(self) -> list[dict]:
        """Get all publisher declarations with containing files and topics.
        
        Returns publisher information grouped by file name, with each publisher's
        keyExpr (topic).
        
        Returns:
            List of dicts: [{fileName: [{keyExpr: str}, ...]}, ...]
        """
        return '''cpg.call.name(\"declare_publisher\").l
        .groupBy(_.file.name.headOption.getOrElse(\"unknown\"))
        .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "keyExpr" -> c.argument(1).code
        ))
        }'''

    @_json_query_decorator
    def get_subscribers(self) -> list[dict]:
        """Get all subscriber declarations with files, callbacks, and topics.
        
        Returns subscriber information grouped by file name, with each subscriber's
        keyExpr (topic) and callback function name.
        
        Returns:
            List of dicts: [{fileName: [{keyExpr: str, callback: str}, ...]}, ...]
        """
        return '''cpg.call.name(\"declare_subscriber\").l
        .groupBy(_.file.name.headOption.getOrElse(\"unknown\"))
        .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "keyExpr" -> c.argument(1).code,
        "callback" -> c.argument(2).code
        ))
        }'''

    @_json_query_decorator
    def get_callback_control_flows(self, file_name: str, callback_name: str) -> list[dict]:
        """Get control flow information for a callback's put() statements.
        
        For each put() call in the specified callback, retrieves:
        - The keyExpr of the publisher being published to
        - The control flow statements (if/else) wrapping the put call
        
        Note: May not correctly handle session.put() calls.
        
        Args:
            file_name: Name of the file containing the callback
            callback_name: Name of the callback function
            
        Returns:
            List of dicts with keys 'keyExpr' and 'controlFlow'
        """
        return f'''cpg.method("{callback_name}").call.name("put").map {{ v =>
        val recvName = v.receiver.isIdentifier.name.headOption.getOrElse("")
        val fname    = "{file_name}"
        
        val keyExpr = cpg.call
            .name("declare_publisher")
            .where(_.file.nameExact(fname))
            .where(_.inAssignment.argument(1).isIdentifier.nameExact(recvName))
            .argument(1)
            .code
            .headOption
            .getOrElse("")
        
        val controlFlow =
            v.inAst.isControlStructure
            .map(cs => (cs.controlStructureType, cs.condition.code.headOption.getOrElse("")))
            .l
        
        Map(
            "keyExpr"     -> keyExpr,
            "controlFlow" -> controlFlow
        )
        }}
        '''
    
    def close(self) -> None:
        """Close the connection to Joern server.
        
        This is typically called automatically on exit, but can be called
        explicitly if needed.
        """
        logger.debug("Closing Joern connection")
        self._connection._stop()
