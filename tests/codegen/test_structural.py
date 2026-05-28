"""Tests for the structural generators: Stepper, Network, Top."""
import re
import unittest

import networkx as nx

from src.builders.IGBuilder import InterconnectionGraph
from src.codegen._structural import (
    _generate_stepper,
    _generate_network_elt,
    _generate_top_model,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _basic_example_ig() -> InterconnectionGraph:
    """A 3-unit graph matching examples/basic-example/Models/Network.dzn edges."""
    g = nx.MultiDiGraph()
    g.add_node(0)
    g.add_node(1)
    g.add_node(2)
    g.add_edge(0, 1, key="basic/B/A")  # A -> B
    g.add_edge(1, 2, key="basic/C/B")  # B -> C
    g.add_edge(2, 1, key="basic/B/C")  # C -> B
    return InterconnectionGraph(g)


class TestStepper(unittest.TestCase):
    def test_step_interface_and_component(self):
        code = _generate_stepper().to_code()
        self.assertIn("interface IStep", code)
        self.assertIn("out void step();", code)
        self.assertIn("on inevitable: step;", code)
        self.assertIn("component Step", code)
        self.assertIn("provides IStep step;", code)


class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.ig = _basic_example_ig()
        self.unit_by_id = {0: "A", 1: "B", 2: "C"}

    def test_imports_all_units_and_step(self):
        code = _generate_network_elt(self.ig, self.unit_by_id).to_code()
        self.assertIn("import A.dzn;", code)
        self.assertIn("import B.dzn;", code)
        self.assertIn("import C.dzn;", code)
        self.assertIn("import Utils/Step.dzn;", code)

    def test_netctl_interface(self):
        code = _normalize(_generate_network_elt(self.ig, self.unit_by_id).to_code())
        self.assertIn("interface INetCtl", code)
        self.assertIn("in void kick();", code)
        self.assertRegex(code, r"on kick: \{\}")

    def test_per_unit_requires_and_stepper(self):
        code = _generate_network_elt(self.ig, self.unit_by_id, single_stepper=False).to_code()
        self.assertIn("requires IA A;", code)
        self.assertIn("requires IB B;", code)
        self.assertIn("requires IC C;", code)
        self.assertIn("requires IStep s1;", code)
        self.assertIn("requires IStep s2;", code)
        self.assertIn("requires IStep s3;", code)

    def test_edge_routing(self):
        code = _normalize(_generate_network_elt(self.ig, self.unit_by_id).to_code())
        self.assertRegex(code, r"on A\.basic_B_A\(\):\s*B\.basic_B_A\(\);")
        self.assertRegex(code, r"on B\.basic_C_B\(\):\s*C\.basic_C_B\(\);")
        self.assertRegex(code, r"on C\.basic_B_C\(\):\s*B\.basic_B_C\(\);")

    def test_per_unit_step_routing(self):
        code = _normalize(_generate_network_elt(self.ig, self.unit_by_id).to_code())
        self.assertRegex(code, r"on s1\.step\(\):\s*A\.step\(\);")
        self.assertRegex(code, r"on s2\.step\(\):\s*B\.step\(\);")
        self.assertRegex(code, r"on s3\.step\(\):\s*C\.step\(\);")

    def test_single_stepper_collapses_step_dispatch(self):
        code = _normalize(_generate_network_elt(self.ig, self.unit_by_id, single_stepper=True).to_code())
        self.assertIn("requires IStep s;", code)
        # Single trigger that dispatches to every unit's step
        self.assertRegex(code, r"on s\.step\(\):\s*\{[^}]*A\.step\(\);[^}]*B\.step\(\);[^}]*C\.step\(\);[^}]*\}")


class TestTop(unittest.TestCase):
    def setUp(self):
        self.ig = _basic_example_ig()
        self.unit_by_id = {0: "A", 1: "B", 2: "C"}

    def test_system_block_instances(self):
        code = _generate_top_model(self.ig, self.unit_by_id).to_code()
        self.assertIn("Network net;", code)
        self.assertIn("CA A_comp;", code)
        self.assertIn("CB B_comp;", code)
        self.assertIn("CC C_comp;", code)
        self.assertIn("Step s1;", code)
        self.assertIn("Step s2;", code)
        self.assertIn("Step s3;", code)

    def test_bindings(self):
        code = _generate_top_model(self.ig, self.unit_by_id).to_code()
        self.assertIn("net_ctl <=> net.ctl;", code)
        self.assertIn("A_comp.A_top <=> net.A;", code)
        self.assertIn("B_comp.B_top <=> net.B;", code)
        self.assertIn("C_comp.C_top <=> net.C;", code)
        self.assertIn("net.s1 <=> s1.step;", code)
        self.assertIn("net.s2 <=> s2.step;", code)
        self.assertIn("net.s3 <=> s3.step;", code)

    def test_single_stepper(self):
        code = _generate_top_model(self.ig, self.unit_by_id, single_stepper=True).to_code()
        self.assertIn("Step s;", code)
        self.assertIn("net.s <=> s.step;", code)
        self.assertNotIn("Step s1;", code)


if __name__ == "__main__":
    unittest.main()
