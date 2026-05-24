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
from typing import Any

from ._connection import Connection

logger = logging.getLogger(__name__)


def _parse_joern_json(response: str) -> Any:
    """Parse Joern's JSON response, stripping ANSI codes and extracting JSON.
    
    Args:
        response: Raw response from Joern server
        
    Returns:
        Parsed JSON object
        
    Raises:
        ValueError: If response cannot be parsed as valid JSON
    """
    rhs = _clean_joern_repl(response)
    logger.debug(f"Cleaning json: {rhs}")

    if rhs.startswith('"""') and rhs.endswith('"""'):
        rhs = rhs[3:-3].strip()
    elif rhs.startswith('"') and rhs.endswith('"'):
        rhs = rhs[1:-1].encode("utf-8").decode("unicode_escape").strip()

    match = re.search(r'([\[\{].*[\]\}])', rhs, re.DOTALL)
    if match:
        rhs = match.group(1)

    try:
        clean = json.loads(rhs)
        logger.debug(f"Cleaned json: {clean}")
        return clean
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse Joern JSON: {exc}") from exc
    
def _clean_joern_repl(response: str) -> str:
    logger.debug(f"Cleaning repl: {response}")
    clean_resp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', response)
    rhs = clean_resp.split("=", 1)[-1].strip() if "=" in clean_resp else clean_resp.strip()
    logger.debug(f"Cleaned: {rhs}")
    return rhs


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

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
    
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
    def _query(func):
        """Decorator for executing a Joern query that returns JSON.
        
        Decorated function should return a Joern query string.
        The decorator executes the query with .toJson, parses the response,
        and returns the parsed JSON object.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            query_res = self._send_query(result + ".toJson")
            return _parse_joern_json(query_res)
        return wrapper

    @_query
    def open_project(self, project_name: str):
        """Load a project by name into the Joern workspace.
        
        Args:
            project_name: Name of the project to open
            
        Returns:
            Response from Joern
        """
        logger.debug(f"Opening Joern project: {project_name}")
        return f'open("{project_name}")'
    
    @_query
    def import_code(self, input_path: str, project_name: str):
        logger.debug(f"Importing code from {input_path}")
        return f'importCode(inputPath="{input_path}", projectName="{project_name}")'
    
    @_query
    def get_var_publishers(self, file_name: str) -> list[dict]:
        """Get (variable name, topic) info for all publishers in a file."""
        return f'''cpg.call.name("declare_publisher")
        .where(_.file.name("{file_name}"))
        .map {{ c => 
        (c.inAssignment.target.code.head, c.argument(1).code) 
        }}'''
    
    @_query
    def get_session_variables(self, file_name: str):
        return f'''cpg.call.code(".*zenoh::Session::open\\\\(.*")
        .where(_.file.name("{file_name}"))
        .inAssignment.target.code.map {{ 
            sessionVar =>
            val putArgs = cpg.call.name("put").where(_.argument(0).codeExact(sessionVar)).argument(1).code.l
            (sessionVar, putArgs)
        }}.toMap'''
    

    @_query
    def get_cfg_as_dot(self, file_name: str, function_name: str):
        logger.debug(f"Retrieved CFG for {function_name} from {file_name}")
        return f"cpg.method.filename(\"{file_name}\").name(\"{function_name}\").dotCfg"

    @_query
    def get_files(self):
        return "cpg.file.name(\".*\\\\.cpp\").map(_.name)"

    @_query
    def get_callback_control_flows(self, file_name: str) -> list[dict]:
        return f"""cpg.call("declare_subscriber").where(_.file.name("{file_name}")).map {{ subCall =>
        val topic = subCall.argument(1).code
        val cbArgCode = subCall.argument(2).code
      
        // Clean up the variable name (e.g., from "&A_callback" to "A_callback")
        val cbVarName = cbArgCode.replace("&", "").trim
      
        // Find the function with the name equal to cbVarName and get its dotCfg
        // If there is no dotCfg, find the assignment where LHS is this variable, get its RHS, 
        // extract the MethodRef, trace it to the Method, and generate the CFG.
      
                val resolvedMethods = {{
                    val directMethods = cpg.method.name(cbVarName).l
                    if (directMethods.nonEmpty) directMethods
                    else {{
                        cpg.assignment
                        .where(_.argument(1).codeExact(cbVarName))
                        .argument(2)
                        .ast.isMethodRef
                        .filter(_.refOut.nonEmpty)
                        .referencedMethod
                        .l
                    }}
                }}

                val resolved = resolvedMethods.headOption
                val callbackFullName = resolved.map(_.fullName).getOrElse(cbVarName)
                val dotGraph = resolved
                    .map(_.dotCfg.headOption.getOrElse("CFG resolution failed"))
                    .getOrElse("CFG resolution failed")
      
                Map(
                        "topic"     -> topic,
                        "callback"  -> cbVarName,
                        "dotGraph"  -> dotGraph
                )
            }}"""
    
    def close(self) -> None:
        """Close the connection to Joern server.
        
        This is typically called automatically on exit, but can be called
        explicitly if needed.
        """
        logger.debug("Closing Joern connection")
        self._connection._stop()
