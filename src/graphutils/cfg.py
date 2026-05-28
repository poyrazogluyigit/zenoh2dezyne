"""DOT parsing utilities for Joern CFGs."""
import networkx as nx

from .dot_parser import parse_dot_to_graph
from ._parse_html import _prettify_labels

class JoernCFG:
    def __init__(self, raw_dot: str):
        self.graph, self.error = parse_dot_to_graph(raw_dot)

        if self.error:
            raise ValueError(f"Failed to parse CFG: {self.error}")
        
        if self.graph:
            self._clean_node_data()
            self.source = self._find_method_entry()
            self._clean_node_ids()
            # reset source after cleaning node IDs
            self.source = 1
            self.num_nodes = self.graph.number_of_nodes()

    def get_type(self, node_id: int) -> str:
        """Returns the node type for the given node ID."""
        if self.graph and node_id in self.graph:
            return self.graph.nodes[node_id].get("node_type")
        else:
            raise ValueError(f"Node ID {node_id} not found in CFG")
        
    def get_data(self, node_id: int) -> dict:
        """Returns the data dictionary for the given node ID."""
        if self.graph and node_id in self.graph:
            return self.graph.nodes[node_id]
        else:
            raise ValueError(f"Node ID {node_id} not found in CFG")
        
    def get_data(self, node_id: int, key: str):
        """Returns the value for the specified key in the node's data dictionary."""
        if self.graph and node_id in self.graph:
            return self.graph.nodes[node_id].get(key)
        else:
            raise ValueError(f"Node ID {node_id} or key {key} not found in CFG")

    def get_successors(self, node_id: int) -> list[int]:
        """Returns a list of successor node IDs for the given node ID."""
        if self.graph and node_id in self.graph:
            return list(self.graph.successors(node_id))
        else:
            raise ValueError(f"Node ID {node_id} not found in CFG")
        
    def get_predecessors(self, node_id: int) -> list[int]:
        """Returns a list of predecessor node IDs for the given node ID."""
        if self.graph and node_id in self.graph:
            return list(self.graph.predecessors(node_id))
        else:
            raise ValueError(f"Node ID {node_id} not found in CFG")
        

    def _find_method_entry(self) -> int:
        """Finds the entry node of the CFG, which is typically the METHOD type node.
        Returns the node ID of the entry node, or None if not found."""
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'METHOD':
                return node
        raise ValueError("No METHOD node found in CFG")

    def __iter__(self):
        """Allows iteration over graph nodes. Provides a high-level
        view for nodes in the graph. Starts automatically from METHOD type node."""
        if self.graph:
            ordered_ids = list(nx.dfs_preorder_nodes(self.graph, source=self.source))
            for node_id in ordered_ids:
                yield node_id
        else:
            return iter([])
        
    def items(self):
        """Returns an iterable of (node_id, node_data) tuples."""
        if self.graph:
            return self.graph.nodes(data=True)
        else:
            return []
            
    def _clean_node_ids(self):
        """Relabel each node with a clean integer ID, starting from 1.
        The entry node is assigned ID 1, and subsequent nodes are numbered sequentially.
        """
        if not self.graph or len(self.graph) == 0:
            return

        ordered_nodes = list(nx.dfs_preorder_nodes(self.graph, self.source))

        # Handle any disconnected subgraphs/nodes that weren't reachable from the entry node
        unreachable_nodes = [n for n in self.graph.nodes() if n not in ordered_nodes]
        ordered_nodes.extend(unreachable_nodes)

        # Create the mapping {old_node_id: new_integer_id}
        mapping = {
            old_node: new_id 
            for new_id, old_node in enumerate(ordered_nodes, start=1)
        }

        # Apply the mapping to the graph
        self.graph = nx.relabel_nodes(self.graph, mapping)

    def _clean_node_data(self):
        """Parses Joern's raw DOT labels to extract clean code and metadata.
        Unescapes HTML entities and splits metadata from the actual code snippet.
        """
        _prettify_labels(self.graph.nodes(data=True))
            

