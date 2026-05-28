import networkx as nx

from dataclasses import dataclass, field

from ..datatypes import TranslationUnit

# Interconnection generation:
# Input: A list of translation units
# Output: Directed graph data structure
#           Vertices: Nodes in the system
#           Edges: Vertex A -> Vertex B <=> A publishes to B
# Generation algorithm: Two passes
# First pass: 
# For each translation unit:
#   Generate vertex of the graph
# Second pass:
# For each translation unit:
#   Add directed edges corresponding to its published topics
# We need ordered tuples for adding these directed edges

@dataclass
class IGNode:
    id: int
    unit: TranslationUnit

class InterconnectionGraph:
    graph: nx.MultiDiGraph

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
    
    def __iter__(self):
        return iter(self.graph.nodes(data=True))
    
    def getSuccessors(self, node_id: int) -> list[int]:
        """Returns a list of successor node IDs for the given node ID."""
        if node_id in self.graph:
            return list(self.graph.successors(node_id))
        else:
            raise ValueError(f"Node ID {node_id} not found in Interconnection Graph")
    
    def getPredecessors(self, node_id: int) -> list[int]:
        """Returns a list of predecessor node IDs for the given node ID."""
        if node_id in self.graph:
            return list(self.graph.predecessors(node_id))
        else:
            raise ValueError(f"Node ID {node_id} not found in Interconnection Graph")
    


class IGBuilder:
    def __init__(self, translation_units: list[TranslationUnit]):
        self.translation_units = translation_units

    # FIXME very unoptimized
    def build(self) -> nx.MultiDiGraph:
        graph = nx.MultiDiGraph()
        for i in range(len(self.translation_units)):
            graph.add_node(i, data=self.translation_units[i])
        for topic, src, sink in self._get_edges():
            src_index = self.translation_units.index(src)
            sink_index = self.translation_units.index(sink)
            graph.add_edge(src_index, sink_index, key=topic)
        return graph
    
    def _get_in_topics_of(self, unit: TranslationUnit) -> set[str]:
        return set(cb.key_expr for cb in unit.callback_threads)

    def _get_out_topics_of(self, unit: TranslationUnit) -> set[str]:
        out_topics = [vp.key_expr for vp in unit.var_publishers]
        for sp in unit.sess_publishers:
            out_topics += sp.key_exprs
        return set(out_topics)

    # TODO control publishing edges that do not have a corresponding subscriber
    def _get_out_edges_of(self, unit: TranslationUnit) -> list[tuple[str, TranslationUnit, TranslationUnit]]:
        out_edges = []
        unit_out_topics = self._get_out_topics_of(unit)
        for target_unit in self.translation_units:
            target_in_topics = self._get_in_topics_of(target_unit)
            for x in (unit_out_topics & target_in_topics):
                out_edges.append((x, unit, target_unit))
        return out_edges
    
    def _get_edges(self) -> list[tuple[str, TranslationUnit, TranslationUnit]]:
        edges = []
        for unit in self.translation_units:
            edges.extend(
                self._get_out_edges_of(unit)
            )
        return edges


