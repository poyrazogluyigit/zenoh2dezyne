"""End-to-end test: drive CodeGenerator with a mocked InterconnectionGraph
and assert every expected file shows up in the output directory."""
import os
import tempfile
import unittest

import networkx as nx

from src.builders.IGBuilder import InterconnectionGraph
from src.codegen import CodeGenerator
from src.datatypes import (
    TranslationUnit, MainThread, CallbackThread,
    VarPublisher, SessPublisher,
)
from src.graphutils import JoernCFG

from ..mock_data import main_flow, put_callback


def _make_tu(file_name: str) -> TranslationUnit:
    return TranslationUnit(
        file_name=file_name,
        main_thread=MainThread(cfg=JoernCFG(main_flow)),
        callback_threads=[
            CallbackThread(name="callback", key_expr="basic/X/Y", cfg=JoernCFG(put_callback))
        ],
        var_publishers=[VarPublisher(var="A_pub", key_expr="example/topic/var_out")],
        sess_publishers=[SessPublisher(var="session", key_exprs=["example/topic/session_out"])],
    )


class TestEndToEnd(unittest.TestCase):
    def test_generate_writes_all_files(self):
        tu_a = _make_tu("A.cpp")
        tu_b = _make_tu("B.cpp")
        g = nx.MultiDiGraph()
        g.add_node(0, data=tu_a)
        g.add_node(1, data=tu_b)
        ig = InterconnectionGraph(g)

        with tempfile.TemporaryDirectory() as out:
            cg = CodeGenerator(out)
            cg.generate(ig)
            cg.printToOutput()

            self.assertTrue(os.path.isfile(os.path.join(out, "A.dzn")))
            self.assertTrue(os.path.isfile(os.path.join(out, "B.dzn")))
            self.assertTrue(os.path.isfile(os.path.join(out, "Network.dzn")))
            self.assertTrue(os.path.isfile(os.path.join(out, "Top.dzn")))
            self.assertTrue(os.path.isfile(os.path.join(out, "Utils", "Step.dzn")))

    def test_generate_emits_per_unit_provides(self):
        tu = _make_tu("MyUnit.cpp")
        g = nx.MultiDiGraph()
        g.add_node(0, data=tu)
        ig = InterconnectionGraph(g)

        with tempfile.TemporaryDirectory() as out:
            cg = CodeGenerator(out)
            cg.generate(ig)
            cg.printToOutput()
            with open(os.path.join(out, "MyUnit.dzn")) as fp:
                content = fp.read()
            self.assertIn("interface IMyUnit", content)
            self.assertIn("component CMyUnit", content)
            self.assertIn("provides IMyUnit MyUnit_top;", content)

    def test_top_model_instantiates_every_unit(self):
        tu_a = _make_tu("A.cpp")
        tu_b = _make_tu("B.cpp")
        g = nx.MultiDiGraph()
        g.add_node(0, data=tu_a)
        g.add_node(1, data=tu_b)
        ig = InterconnectionGraph(g)

        with tempfile.TemporaryDirectory() as out:
            cg = CodeGenerator(out)
            cg.generate(ig)
            cg.printToOutput()
            with open(os.path.join(out, "Top.dzn")) as fp:
                content = fp.read()
            self.assertIn("CA A_comp;", content)
            self.assertIn("CB B_comp;", content)


if __name__ == "__main__":
    unittest.main()
