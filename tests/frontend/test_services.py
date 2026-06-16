"""Tests for request/reply (service) extraction across middlewares."""
import unittest

from src.datatypes import ServiceEndpoint
from src.frontend.extractors import ZenohExtractor, Ros1Extractor, Ros2Extractor


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


class TestRos2Services(unittest.TestCase):
    def test_server_and_client(self):
        client = FakeJoernClient({
            "create_service": [{"srv_": ['"set_bool"']}],
            "create_client": [{"client_": ['"set_bool"']}],
        })
        svcs = Ros2Extractor().extract_services(client, "node.cpp")
        roles = {(s.role, s.name) for s in svcs}
        self.assertIn(("server", '"set_bool"'), roles)
        self.assertIn(("client", '"set_bool"'), roles)
        self.assertTrue(all(isinstance(s, ServiceEndpoint) for s in svcs))


class TestRos1Services(unittest.TestCase):
    def test_server_and_client(self):
        client = FakeJoernClient({
            "advertiseService": [{"srv_": ['"set_bool"']}],
            "serviceClient": [{"client_": ['"set_bool"']}],
        })
        svcs = Ros1Extractor().extract_services(client, "node.cpp")
        roles = {(s.role, s.name) for s in svcs}
        self.assertIn(("server", '"set_bool"'), roles)
        self.assertIn(("client", '"set_bool"'), roles)


class TestZenohServices(unittest.TestCase):
    def test_queryable_server_and_get_client(self):
        client = FakeJoernClient({
            "declare_queryable": ['"myhome/kitchen/temp"'],
            'name("get")': ['"myhome/kitchen/*"'],
        })
        svcs = ZenohExtractor().extract_services(client, "node.cpp")
        roles = {(s.role, s.name) for s in svcs}
        self.assertIn(("server", '"myhome/kitchen/temp"'), roles)
        self.assertIn(("client", '"myhome/kitchen/*"'), roles)
        # the get-client query must be scoped to the discovered session variable
        get_query = next(q for q in client.queries if 'name("get")' in q)
        self.assertIn("codeExact", get_query)


class TestNoServicesByDefault(unittest.TestCase):
    def test_empty_when_none_present(self):
        client = FakeJoernClient({})
        self.assertEqual(ZenohExtractor().extract_services(client, "x.cpp"), [])
        self.assertEqual(Ros2Extractor().extract_services(client, "x.cpp"), [])


if __name__ == "__main__":
    unittest.main()
