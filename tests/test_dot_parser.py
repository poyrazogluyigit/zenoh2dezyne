import unittest
import networkx as nx
from src.graphutils.dot_parser import parse_dot_to_graph, JoernCFG

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

    def test_joern_cfg_invalid(self):
        with self.assertRaisesRegex(ValueError, "Failed to parse CFG: Empty dotCfg"):
            JoernCFG("")

    def test_joern_cfg_valid(self):
        valid_dot = 'digraph "test" { "NodeA" -> "NodeB"; }'
        cfg = JoernCFG(valid_dot)
        
        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)
        
        self.assertEqual(set(cfg.graph.nodes()), {1, 2})
        edges = list(cfg.graph.edges())
        self.assertEqual(len(edges), 1)
        self.assertIn(edges[0], [(1, 2), (2, 1)])

    def test_joern_loop_cfg(self):
        loop_dot = 'digraph "loop" { "Start" -> "Loop"; "Loop" -> "Loop"; "Loop" -> "End"; }'
        cfg = JoernCFG(loop_dot)
        
        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)
        
        self.assertEqual(set(cfg.graph.nodes()), {1, 2, 3})
        edges = list(cfg.graph.edges())
        self.assertEqual(len(edges), 3)
        self.assertIn((1, 2), edges)  # Start -> Loop
        self.assertIn((2, 2), edges)  # Loop -> Loop
        self.assertIn((2, 3), edges)  # Loop -> End

    def test_joern_proper_cfg(self):
        proper_dot = '''digraph \"&lt;lambda&gt;0\" 
        {  \nnode [shape=\"rect\"];  \n\"30064771087\" [label = <put, 19<BR/>A_pub.put(&quot;example payload to A&quot;)> ]\n\"30064771083\" 
        [label = <&lt;operator&gt;.assignment, 16<BR/>i = 0> ]\n\"30064771084\" 
        [label = <&lt;operator&gt;.lessThan, 16<BR/>i &lt; 5> ]\n\"30064771085\" 
        [label = <&lt;operator&gt;.postIncrement, 16<BR/>i++> ]\n\"30064771086\" 
        [label = <put, 17<BR/>C_pub.put(&quot;example payload to C&quot;)> ]\n\"107374182404\" 
        [label = <METHOD, 15<BR/>&lt;lambda&gt;0> ]\n\"124554051587\" [label = <METHOD_RETURN, 15<BR/>void> ]\n  
        \"30064771087\" -> \"124554051587\" \n  \"30064771083\" -> \"30064771084\" \n  
        \"30064771084\" -> \"30064771086\" \n  \"30064771084\" -> \"30064771087\" \n  \"30064771085\" -> \"30064771084\" 
        \n  \"30064771086\" -> \"30064771085\" \n  \"107374182404\" -> \"30064771083\" \n}\n'''

        cfg = JoernCFG(proper_dot)
        self.assertIsNone(cfg.error)
        self.assertIsNotNone(cfg.graph)
        self.assertIsInstance(cfg.graph, nx.DiGraph)

        self.assertEqual(set(cfg.graph.nodes()), {1, 2, 3, 4, 5, 6, 7})
        edges = list(cfg.graph.edges())
        print(cfg.graph.nodes(data=True))
        self.assertEqual(len(edges), 7)
        self.assertIn((5, 3), edges)
        self.assertIn((3, 6), edges)


if __name__ == "__main__":
    unittest.main()
