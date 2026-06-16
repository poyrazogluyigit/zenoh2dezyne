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
        normalize_publish_nodes(self.cfg, ZenohExtractor(), self.publishers)
        publish_nodes = [n for n in self.cfg if self.cfg.get_type(n) == "put"]
        self.assertTrue(publish_nodes)
        for n in publish_nodes:
            self.assertEqual(self.cfg.get_data(n, "comm_op"), "publish")
            self.assertIsNotNone(self.cfg.get_data(n, "topic"))

    def test_resolves_handle_and_session_topics(self):
        normalize_publish_nodes(self.cfg, ZenohExtractor(), self.publishers)
        topics = {
            self.cfg.get_data(n, "topic")
            for n in self.cfg
            if self.cfg.get_type(n) == "put"
        }
        self.assertIn("example/topic/var_out", topics)        # handle A_pub → declared topic
        self.assertIn("example/topic/session_out", topics)    # session.put literal

    def test_non_publish_nodes_untouched(self):
        normalize_publish_nodes(self.cfg, ZenohExtractor(), self.publishers)
        non_publish = [n for n in self.cfg if self.cfg.get_type(n) != "put"]
        for n in non_publish:
            self.assertIsNone(self.cfg.get_data(n, "comm_op"))


if __name__ == "__main__":
    unittest.main()
