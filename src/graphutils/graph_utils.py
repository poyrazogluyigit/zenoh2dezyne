"""DOT parsing utilities for Joern CFGs."""
from typing import Optional, Tuple
from dataclasses import field, dataclass
import networkx as nx
import pydot


def parse_dot_to_graph(dot: str):
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
            self._clean_node_ids()
            self._prettify_labels()
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

    def _find_method_entry(self) -> Optional[int]:
        """Finds the entry node of the CFG, which is typically the METHOD type node.
        Returns the node ID of the entry node, or None if not found."""
        for node_id, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'METHOD':
                return node_id
        return None

    def __iter__(self):
        """Allows iteration over graph nodes. Provides a high-level
        view for nodes in the graph. Starts automatically from METHOD type node."""
        if self.graph:
            source = self._find_method_entry()
            if source is not None:
               ordered_ids = list(nx.dfs_preorder_nodes(self.graph, source=source))
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

        # 1. Identify the entry node(s). In a CFG, the entry node has an in-degree of 0.
        roots = [n for n, d in self.graph.in_degree() if d == 0]
        entry_node = roots[0] if roots else list(self.graph.nodes())[0]

        # 2. Traverse the graph starting from the entry node.
        ordered_nodes = list(nx.dfs_preorder_nodes(self.graph, source=entry_node))

        # 3. Handle any disconnected subgraphs/nodes that weren't reachable from the entry node
        unreachable_nodes = [n for n in self.graph.nodes() if n not in ordered_nodes]
        ordered_nodes.extend(unreachable_nodes)

        # 4. Create the mapping {old_node_id: new_integer_id}
        mapping = {
            old_node: new_id 
            for new_id, old_node in enumerate(ordered_nodes, start=1)
        }

        # 5. Apply the mapping to the graph
        self.graph = nx.relabel_nodes(self.graph, mapping)

    def _prettify_labels(self):
        import html
        import re
        """Parses Joern's raw DOT labels to extract clean code and metadata.
        Unescapes HTML entities and splits metadata from the actual code snippet.
        """
        for node, data in self.graph.nodes(data=True):
            raw_label = data.get('label', '')
            if not raw_label:
                continue

            # 1. Strip the outer GraphViz brackets/quotes
            # e.g., '"<put, 19<BR/>A_pub.put(...)>"' -> 'put, 19<BR/>A_pub.put(...)'
            clean_label = raw_label.strip('<>').strip('"').strip('<>')

            # 2. Joern separates the metadata from the code snippet with a <BR/> tag
            parts = re.split(r'<BR/>', clean_label, flags=re.IGNORECASE)

            if len(parts) == 2:
                # Format is usually: "NodeType, LineNumber" <BR/> "CodeSnippet"
                meta_part, code_part = parts
                
                # Split the metadata into Node Type and Line Number
                meta_splits = meta_part.rsplit(',', 1)
                node_type = meta_splits[0].strip()
                line_number = meta_splits[1].strip() if len(meta_splits) > 1 else ""

                # 3. Unescape HTML entities (e.g., &quot; -> ", &lt; -> <)
                clean_code = html.unescape(code_part.strip())
                clean_type = html.unescape(node_type.strip())

                # 4. Inject the parsed data as new, clean attributes on the node
                # data['code'] = clean_code
                data['node_type'] = clean_type
                # data['line_number'] = line_number
                
                # 5. Overwrite the ugly 'label' with the clean code for easy string matching
                data['label'] = clean_code

            else:
                # Fallback for nodes that don't have a <BR/> tag
                clean_code = html.unescape(clean_label.strip())
                data['code'] = clean_code
                data['label'] = clean_code
            

