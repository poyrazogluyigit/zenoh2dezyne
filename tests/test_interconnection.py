import unittest
import networkx as nx

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.interconnect_test_data import mock_unit_A, mock_unit_B

from src.builders.IGBuilder import IGBuilder

class _StubTUBuilder:
    def __init__(self, units):
        self._units = units

    def build(self):
        return self._units


class TestInterconnection(unittest.TestCase):

    def setUp(self):
        self.data = [mock_unit_A, mock_unit_B]
        self.builder = IGBuilder(_StubTUBuilder(self.data))

    def test_in_out_topics(self):
        self.assertEqual(self.builder._get_in_topics_of(mock_unit_A), {"example/B_to_A"})
        self.assertEqual(self.builder._get_out_topics_of(mock_unit_A), {"example/A_to_B"})
        self.assertEqual(self.builder._get_in_topics_of(mock_unit_B), {"example/A_to_B"})
        self.assertEqual(self.builder._get_out_topics_of(mock_unit_B), {"example/B_to_A"})

    def test_get_edges(self):
        edges = self.builder._get_edges()

        self.assertTrue(all(isinstance(edge, tuple) and len(edge) == 3 for edge in edges))

        expected_edges = [
            ("example/A_to_B", mock_unit_A, mock_unit_B),
            ("example/B_to_A", mock_unit_B, mock_unit_A),
        ]
        self.assertEqual(edges, expected_edges)

    def test_interconnection_graph(self):
        graph = self.builder.build()

        self.assertIsInstance(graph, nx.MultiDiGraph)
        self.assertEqual(set(graph.nodes()), set(range(len(self.data))))

        for node_id, attrs in graph.nodes(data=True):
            self.assertEqual(attrs.get("data"), self.data[node_id])

        idx_a = self.data.index(mock_unit_A)
        idx_b = self.data.index(mock_unit_B)
        expected_edges = [
            (idx_a, idx_b, "example/A_to_B"),
            (idx_b, idx_a, "example/B_to_A"),
        ]
        actual_edges = [
            (src, sink, key)
            for src, sink, key in graph.edges(keys=True)
        ]
        self.assertEqual(actual_edges, expected_edges)