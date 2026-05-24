import unittest
import networkx as nx

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from graphutils import JoernCFG, parse_dot_to_graph

proper_dot = '''digraph "&lt;lambda&gt;0" 
        {  \nnode [shape="rect"];  \n"30064771087" [label = <put, 19<BR/>A_pub.put(&quot;example payload to A&quot;)> ]\n"30064771083" 
        [label = <&lt;operator&gt;.assignment, 16<BR/>i = 0> ]\n"30064771084" 
        [label = <&lt;operator&gt;.lessThan, 16<BR/>i &lt; 5> ]\n"30064771085" 
        [label = <&lt;operator&gt;.postIncrement, 16<BR/>i++> ]\n"30064771086" 
        [label = <put, 17<BR/>C_pub.put(&quot;example payload to C&quot;)> ]\n"107374182404" 
        [label = <METHOD, 15<BR/>&lt;lambda&gt;0> ]\n"124554051587" [label = <METHOD_RETURN, 15<BR/>void> ]\n  
        "30064771087" -> "124554051587" \n  "30064771083" -> "30064771084" \n  
        "30064771084" -> "30064771086" \n  "30064771084" -> "30064771087" \n  "30064771085" -> "30064771084" 
        \n  "30064771086" -> "30064771085" \n  "107374182404" -> "30064771083" \n}\n'''


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
        cfg = self._make_cfg(proper_dot)
        cfg._prettify_labels()

        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        method_node = self._find_node_id_by_type(cfg.graph, "METHOD")
        self.assertIsNotNone(method_node)

    def test_cfg_entry_node(self):
        cfg = self._make_cfg(proper_dot)
        cfg._prettify_labels()

        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        entry = cfg._find_method_entry()
        self.assertIsNotNone(entry)
        self.assertEqual(cfg.graph.nodes[entry].get("node_type"), "METHOD")

    def test_proper_cfg(self):
        cfg = self._make_cfg(proper_dot)
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
        cfg = JoernCFG(proper_dot)

        for _node in cfg:
            pass


if __name__ == "__main__":
    unittest.main()
