"""Tests for CFG publish-node normalization."""
import unittest

from src.graphutils import JoernCFG
from src.datatypes import Publisher
from src.frontend.extractors import ZenohExtractor
from src.builders._normalize import normalize_publish_nodes
from ..mock_data import put_callback


class TestNormalizePublishNodes(unittest.TestCase):
    def setUp(self):
        # put_callback contains: A_pub.put(...) and session.put("example/topic/session_out", ...)
        self.cfg = JoernCFG(put_callback)
        self.publishers = [Publisher(symbol="A_pub", topic="example/topic/var_out")]

    def test_publish_nodes_tagged_with_comm_op_and_topic(self):
        ext = ZenohExtractor()
        ext._session_symbols = {"session"}
        normalize_publish_nodes(self.cfg, ext, self.publishers)
        publish_nodes = [n for n in self.cfg if self.cfg.get_type(n) == "put"]
        self.assertTrue(publish_nodes)
        for n in publish_nodes:
            self.assertEqual(self.cfg.get_data(n, "comm_op"), "publish")
            self.assertIsNotNone(self.cfg.get_data(n, "topic"))

    def test_resolves_handle_and_session_topics(self):
        ext = ZenohExtractor()
        ext._session_symbols = {"session"}  # populated by extract_publishers in real flow
        normalize_publish_nodes(self.cfg, ext, self.publishers)
        topics = {
            self.cfg.get_data(n, "topic")
            for n in self.cfg
            if self.cfg.get_type(n) == "put"
        }
        self.assertIn("example/topic/var_out", topics)        # handle A_pub → declared topic
        self.assertIn("example/topic/session_out", topics)    # session.put literal

    def test_resolves_session_put_for_renamed_session_var(self):
        # Session bound to `s` (not `session`): the literal key-expr must still resolve.
        renamed_cfg = JoernCFG(
            'digraph "cb" {\n'
            'node [shape="rect"];\n'
            '"1" [label = <METHOD, 1<BR/>cb> ]\n'
            '"2" [label = <put, 2<BR/>s.put("renamed/topic", "payload")> ]\n'
            '"3" [label = <METHOD_RETURN, 1<BR/>void> ]\n'
            '"1" -> "2"\n'
            '"2" -> "3"\n'
            '}'
        )
        ext = ZenohExtractor()
        ext._session_symbols = {"s"}
        normalize_publish_nodes(renamed_cfg, ext, [])
        topics = {
            renamed_cfg.get_data(n, "topic")
            for n in renamed_cfg
            if renamed_cfg.get_type(n) == "put"
        }
        self.assertIn("renamed/topic", topics)

    def test_non_publish_nodes_untouched(self):
        normalize_publish_nodes(self.cfg, ZenohExtractor(), self.publishers)
        non_publish = [n for n in self.cfg if self.cfg.get_type(n) != "put"]
        for n in non_publish:
            self.assertIsNone(self.cfg.get_data(n, "comm_op"))


if __name__ == "__main__":
    unittest.main()
