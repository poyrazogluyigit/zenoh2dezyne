"""Tests for ROS1 and ROS2 extractors.

ROS templated calls (``create_publisher<T>(...)``) are misparsed by Joern's
fuzzy C++ frontend into field-access + comparison operators, so extraction
anchors on the enclosing assignment and recovers the topic from string
literals / the callback from the code. These tests pin that contract.
"""
import unittest

from src.datatypes import Publisher
from src.frontend.extractors import Ros1Extractor, Ros2Extractor, get_extractor
from ..mock_data import put_callback


class FakeJoernClient:
    def __init__(self, responses: dict[str, object]):
        self._responses = responses
        self.queries: list[str] = []

    def run_query(self, scala: str):
        self.queries.append(scala)
        for marker, payload in self._responses.items():
            if marker in scala:
                return payload
        return []


class TestRos2Extractor(unittest.TestCase):
    def test_publishers_from_assignment_literals(self):
        client = FakeJoernClient({
            "create_publisher": [{"chatter_pub": ['"chatter"', "10"]}],
        })
        pubs = Ros2Extractor().extract_publishers(client, "talker.cpp")
        self.assertEqual(pubs, [Publisher(symbol="chatter_pub", topic='"chatter"')])

    def test_subscribers_parsed_from_code_plus_cfg_lookup(self):
        client = FakeJoernClient({
            "create_subscription": [
                'sub = node->create_subscription<std_msgs::msg::String>("chatter", 10, &topic_callback)'
            ],
            "dotCfg": [put_callback],
        })
        subs = Ros2Extractor().extract_subscribers(client, "listener.cpp")
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0].name, "topic_callback")
        self.assertEqual(subs[0].topic, '"chatter"')
        self.assertIsNotNone(subs[0].cfg)

    def test_publish_call_names(self):
        self.assertEqual(Ros2Extractor().publish_call_names, frozenset({"publish"}))

    def test_resolve_publish_topic_via_handle_arrow(self):
        ext = Ros2Extractor()
        pubs = [Publisher(symbol="chatter_pub", topic="chatter")]
        self.assertEqual(ext.resolve_publish_topic("chatter_pub->publish(msg)", pubs), "chatter")

    def test_registry(self):
        self.assertIsInstance(get_extractor("ros2"), Ros2Extractor)


class TestRos1Extractor(unittest.TestCase):
    def test_publishers_from_assignment_literals(self):
        client = FakeJoernClient({
            "advertise": [{"chatter_pub": ['"chatter"', "1000"]}],
        })
        pubs = Ros1Extractor().extract_publishers(client, "talker.cpp")
        self.assertEqual(pubs, [Publisher(symbol="chatter_pub", topic='"chatter"')])

    def test_subscribers_parsed_from_code_plus_cfg_lookup(self):
        client = FakeJoernClient({
            "subscribe": ['sub = nh.subscribe("chatter", 1000, chatterCallback)'],
            "dotCfg": [put_callback],
        })
        subs = Ros1Extractor().extract_subscribers(client, "listener.cpp")
        self.assertEqual(subs[0].name, "chatterCallback")
        self.assertEqual(subs[0].topic, '"chatter"')

    def test_resolve_publish_topic_via_handle_dot(self):
        ext = Ros1Extractor()
        pubs = [Publisher(symbol="chatter_pub", topic="chatter")]
        self.assertEqual(ext.resolve_publish_topic("chatter_pub.publish(msg)", pubs), "chatter")

    def test_publisher_symbol_strips_joern_scope_prefix(self):
        # Joern reports global-scope handles as "<global> name". The stored symbol
        # must be the bare identifier so it matches the bare publish receiver
        # (`name.publish(...)`); otherwise the topic never resolves.
        client = FakeJoernClient({
            "advertise": [{"<global> chatter_pub": ['"/chatter"', "1", "true"]}],
        })
        pubs = Ros1Extractor().extract_publishers(client, "talker.cpp")
        self.assertEqual(pubs, [Publisher(symbol="chatter_pub", topic='"/chatter"')])
        # And it now resolves against a bare receiver:
        self.assertEqual(
            Ros1Extractor().resolve_publish_topic("chatter_pub.publish(m)", pubs), '"/chatter"'
        )

    def test_registry(self):
        self.assertIsInstance(get_extractor("ros1"), Ros1Extractor)


if __name__ == "__main__":
    unittest.main()
