import unittest
import networkx as nx

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.graphutils import JoernCFG, parse_dot_to_graph
from tests.mock_data import looping_callback


class TestCFG(unittest.TestCase):

    def _make_cfg(self, dot):
        cfg = JoernCFG.__new__(JoernCFG)
        cfg.graph, cfg.error = parse_dot_to_graph(dot)
        return cfg

    def _find_node_id_by_type(self, graph, node_type):
        for node_id, data in graph.nodes(data=True):
            if data.get("node_type") == node_type:
                return node_id
        return None

    def test_joern_cfg_invalid(self):
        with self.assertRaisesRegex(ValueError, "Failed to parse CFG: Empty dotCfg"):
            JoernCFG("")

    def test_cfg_valid(self):
        valid_dot = 'digraph "test" { "NodeA" -> "NodeB"; }'
        cfg = self._make_cfg(valid_dot)

        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        self.assertEqual(set(cfg.graph.nodes()), {"NodeA", "NodeB"})
        edges = list(cfg.graph.edges())
        self.assertEqual(len(edges), 1)
        self.assertIn(edges[0], [("NodeA", "NodeB")])

    def test_cfg_labeling(self):
        cfg = self._make_cfg(looping_callback)
        cfg._prettify_labels()

        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        method_node = self._find_node_id_by_type(cfg.graph, "METHOD")
        self.assertIsNotNone(method_node)

    def test_cfg_entry_node(self):
        cfg = self._make_cfg(looping_callback)
        cfg._prettify_labels()

        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        entry = cfg._find_method_entry()
        self.assertIsNotNone(entry)
        self.assertEqual(cfg.graph.nodes[entry].get("node_type"), "METHOD")

    def test_proper_cfg(self):
        cfg = self._make_cfg(looping_callback)
        cfg._prettify_labels()
        cfg.source = self._find_node_id_by_type(cfg.graph, "METHOD")
        self.assertIsNotNone(cfg.source)
        cfg._clean_node_ids()
        cfg.num_nodes = cfg.graph.number_of_nodes()
        cfg._construct_cfg_nodes()

        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        self.assertEqual(set(cfg.graph.nodes()), {1, 2, 3, 4, 5, 6, 7})
        edges = list(cfg.graph.edges())
        self.assertEqual(len(edges), 7)
        self.assertIn((5, 3), edges)
        self.assertIn((3, 6), edges)

    def test_cfg_iter(self):
        cfg = JoernCFG(looping_callback)

        for _node in cfg:
            pass


if __name__ == "__main__":
    unittest.main()
