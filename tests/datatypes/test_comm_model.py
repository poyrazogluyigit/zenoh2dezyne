"""Tests for the neutral (middleware-agnostic) communication model datatypes."""
import unittest

from src.datatypes import (
    Publisher,
    Subscriber,
    ServiceEndpoint,
    TranslationUnit,
    MainThread,
)


class TestCommModel(unittest.TestCase):
    def test_publisher_has_symbol_and_topic(self):
        p = Publisher(symbol="A_pub", topic="basic/B/A")
        self.assertEqual(p.symbol, "A_pub")
        self.assertEqual(p.topic, "basic/B/A")

    def test_subscriber_has_name_topic_cfg(self):
        s = Subscriber(name="A_callback", topic="basic/B/A", cfg=None)
        self.assertEqual(s.name, "A_callback")
        self.assertEqual(s.topic, "basic/B/A")
        self.assertIsNone(s.cfg)

    def test_service_endpoint_roles(self):
        server = ServiceEndpoint(role="server", name="set_bool", topic="set_bool", cfg=None)
        client = ServiceEndpoint(role="client", name="set_bool", topic="set_bool", cfg=None)
        self.assertEqual(server.role, "server")
        self.assertEqual(client.role, "client")
        self.assertEqual(server.name, "set_bool")

    def test_translation_unit_neutral_fields(self):
        pub = Publisher(symbol="A_pub", topic="basic/B/A")
        sub = Subscriber(name="cb", topic="basic/C/A", cfg=None)
        svc = ServiceEndpoint(role="server", name="svc", topic="svc", cfg=None)
        tu = TranslationUnit(
            file_name="A.cpp",
            main_thread=MainThread(cfg=None),
            callback_threads=[sub],
            publishers=[pub],
            services=[svc],
        )
        self.assertEqual(tu.publishers, [pub])
        self.assertEqual(tu.callback_threads, [sub])
        self.assertEqual(tu.services, [svc])

    def test_translation_unit_defaults_empty(self):
        tu = TranslationUnit(file_name="A.cpp", main_thread=MainThread(cfg=None))
        self.assertEqual(tu.publishers, [])
        self.assertEqual(tu.callback_threads, [])
        self.assertEqual(tu.services, [])


if __name__ == "__main__":
    unittest.main()
