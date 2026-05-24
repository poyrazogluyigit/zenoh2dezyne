import unittest
import networkx as nx

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from graphutils import parse_dot_to_graph


class TestDotParser(unittest.TestCase):

    def test_parse_dot_empty_or_none(self):
        graph, err = parse_dot_to_graph("")
        self.assertIsNone(graph)
        self.assertEqual(err, "Empty dotCfg")

        graph, err = parse_dot_to_graph("   ")
        self.assertIsNone(graph)
        self.assertEqual(err, "Empty dotCfg")

        graph, err = parse_dot_to_graph(None)
        self.assertIsNone(graph)
        self.assertEqual(err, "Empty dotCfg")

    def test_parse_dot_resolution_failed(self):
        graph, err = parse_dot_to_graph("some output containing CFG resolution failed inside")
        self.assertIsNone(graph)
        self.assertEqual(err, "CFG resolution failed on Joern side")

    def test_parse_dot_invalid(self):
        graph, err = parse_dot_to_graph("this is not a valid dot string")
        self.assertIsNone(graph)
        self.assertEqual(err, "Invalid DOT string")

    def test_parse_dot_valid(self):
        valid_dot = 'digraph "my_graph" { A -> B; B -> C; }'
        graph, err = parse_dot_to_graph(valid_dot)
        self.assertIsNone(err)
        self.assertIsInstance(graph, nx.DiGraph)
        self.assertEqual(set(graph.nodes()), {'A', 'B', 'C'})
        self.assertEqual(list(graph.edges()), [('A', 'B'), ('B', 'C')])

    def test_parse_dot_non_digraph(self):
        valid_dot = 'graph "my_graph" { A -- B; }'
        graph, err = parse_dot_to_graph(valid_dot)
        self.assertIsNone(err)
        self.assertIsInstance(graph, nx.DiGraph)


if __name__ == "__main__":
    unittest.main()
