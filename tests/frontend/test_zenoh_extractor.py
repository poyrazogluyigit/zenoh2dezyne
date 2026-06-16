"""Tests for ZenohExtractor — middleware-specific extraction over a JoernClient."""
import unittest

from src.datatypes import Publisher, Subscriber
from src.frontend.extractors import ZenohExtractor, get_extractor
from ..mock_data import put_callback


class FakeJoernClient:
    """Stand-in for JoernClient: returns canned parsed results keyed by query content."""
    def __init__(self, responses: dict[str, object]):
        self._responses = responses
        self.queries: list[str] = []

    def run_query(self, scala: str):
        self.queries.append(scala)
        for marker, payload in self._responses.items():
            if marker in scala:
                return payload
        return []


class TestZenohExtractor(unittest.TestCase):
    def test_extract_publishers_merges_declared_and_session(self):
        client = FakeJoernClient({
            "declare_publisher": [{"A_pub": '"basic/B/A"'}, {"C_pub": '"basic/C/A"'}],
            "Session::open": [{"session": ['"basic/B/A"']}],
        })
        pubs = ZenohExtractor().extract_publishers(client, "A.cpp")
        self.assertIn(Publisher(symbol="A_pub", topic='"basic/B/A"'), pubs)
        self.assertIn(Publisher(symbol="C_pub", topic='"basic/C/A"'), pubs)
        self.assertIn(Publisher(symbol="session", topic='"basic/B/A"'), pubs)

    def test_extract_subscribers(self):
        client = FakeJoernClient({
            "declare_subscriber": [
                {"topic": '"basic/B/A"', "callback": "A_callback", "dotGraph": put_callback},
            ],
        })
        subs = ZenohExtractor().extract_subscribers(client, "B.cpp")
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].name, "A_callback")
        self.assertEqual(subs[0].topic, '"basic/B/A"')
        self.assertIsNotNone(subs[0].cfg)

    def test_publish_call_names(self):
        self.assertEqual(ZenohExtractor().publish_call_names, frozenset({"put"}))

    def test_registry_resolves_zenoh(self):
        self.assertIsInstance(get_extractor("zenoh"), ZenohExtractor)

    def test_extract_publishers_records_session_symbols(self):
        # Session bound to a non-`session` name must still be discovered.
        client = FakeJoernClient({
            "declare_publisher": [],
            "Session::open": [{"s": ['"renamed/topic"']}],
        })
        ext = ZenohExtractor()
        ext.extract_publishers(client, "A.cpp")
        self.assertEqual(ext._session_symbols, {"s"})

    def test_resolve_uses_discovered_session_not_literal(self):
        ext = ZenohExtractor()
        ext._session_symbols = {"s"}
        # receiver `s` is a session → parse the inline key-expr literal
        self.assertEqual(ext.resolve_publish_topic('s.put("k/expr", payload)', []), "k/expr")
        # bare "session" is NOT special anymore when it isn't a discovered session var
        self.assertIsNone(ext.resolve_publish_topic('session.put("x", payload)', []))


if __name__ == "__main__":
    unittest.main()
