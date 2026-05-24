"""DOT parsing utilities for Joern CFGs."""
from typing import Optional, Tuple
from dataclasses import field, dataclass
import networkx as nx
import html
import re

from .dot_parser import parse_dot_to_graph
from ._parse_html import _prettify_labels

@dataclass
class CFGNode:
    id: int = -1
    node_type: str = ''
    label: str = ''
    predecessors: list[int] = field(default_factory=list)
    successors: list[int] = field(default_factory=list)

    @property
    def is_put(self):
        return self.node_type == "put"
    
    @property
    def is_method_return(self):
        return self.node_type == "METHOD_RETURN"

class JoernCFG:
    def __init__(self, raw_dot: str):
        self.graph, self.error = parse_dot_to_graph(raw_dot)

        if self.error:
            raise ValueError(f"Failed to parse CFG: {self.error}")
        
        if self.graph:
            self._prettify_labels()
            self.source = self._find_method_entry()
            self._clean_node_ids()
            # reset source after cleaning node IDs
            self.source = 1
            self.num_nodes = self.graph.number_of_nodes()
            self._construct_cfg_nodes()

    def _construct_cfg_nodes(self):
        """Constructs CFGNode objects for each node in the graph and stores them in a dictionary."""
        self.cfg_nodes = []
        for node_id in range(1, self.num_nodes + 1):
            data = self.graph.nodes[node_id]
            node = CFGNode(
                id=node_id,
                node_type=data.get('node_type', ''),
                label=data.get('label', '')
            )
            self.cfg_nodes.append(node)

        for node_id in range(1, self.num_nodes + 1):
            current_node = self.cfg_nodes[node_id - 1]
            
            current_node.predecessors = [
                self.cfg_nodes[pred_id - 1] 
                for pred_id in self.graph.predecessors(node_id)
            ]
            
            current_node.successors = [
                self.cfg_nodes[succ_id - 1] 
                for succ_id in self.graph.successors(node_id)
            ]

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
                yield self.cfg_nodes[node_id - 1]
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

    def _prettify_labels(self):
        """Parses Joern's raw DOT labels to extract clean code and metadata.
        Unescapes HTML entities and splits metadata from the actual code snippet.
        """
        _prettify_labels(self.graph.nodes(data=True))
            

