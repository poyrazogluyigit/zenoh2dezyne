"""DOT parsing utilities for Joern CFGs."""
from typing import Optional, Tuple


def parse_dot_to_graph(dot: str):
    """Parse a GraphViz DOT string into a NetworkX DiGraph.

    Returns a tuple of (graph, error_message). If parsing fails,
    graph is None and error_message describes the failure.
    """
    if not dot or not dot.strip():
        return None, "Empty dotCfg"
    if "CFG resolution failed" in dot:
        return None, "CFG resolution failed"

    try:
        import pydot
        import networkx as nx
    except ImportError as exc:
        raise ImportError(
            "DOT parsing requires 'networkx' and 'pydot'. "
            "Install them with: pip install networkx pydot"
        ) from exc

    graphs = pydot.graph_from_dot_data(dot)
    if not graphs:
        return None, "Failed to parse DOT"

    nx_graph = nx.drawing.nx_pydot.from_pydot(graphs[0])
    if not isinstance(nx_graph, nx.DiGraph):
        nx_graph = nx.DiGraph(nx_graph)

    return nx_graph, None
