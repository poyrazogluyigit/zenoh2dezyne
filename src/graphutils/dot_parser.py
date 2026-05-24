"""DOT parsing utilities for Joern CFGs."""
from typing import Any
import networkx as nx
import pydot


def parse_dot_to_graph(dot: str) -> Any:
    """Parse a GraphViz DOT string into a NetworkX DiGraph.

    Returns a tuple of (graph, error_message). If parsing fails,
    graph is None and error_message describes the failure.
    """
    if not dot or not dot.strip():
        return None, "Empty dotCfg"
    if "CFG resolution failed" in dot:
        return None, "CFG resolution failed on Joern side"

    graphs = pydot.graph_from_dot_data(dot)
    if not graphs:
        return None, "Invalid DOT string"

    nx_graph = nx.drawing.nx_pydot.from_pydot(graphs[0])
    if not isinstance(nx_graph, nx.DiGraph):
        nx_graph = nx.DiGraph(nx_graph)

    return nx_graph, None