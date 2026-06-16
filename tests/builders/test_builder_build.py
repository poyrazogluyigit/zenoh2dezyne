import unittest
from unittest import mock
from src.builders import Builder


class TestBuilderBuild(unittest.TestCase):
    def test_build_does_not_import(self):
        client = mock.Mock()
        with mock.patch("src.builders.builder.get_extractor"), \
             mock.patch("src.builders.builder.TUBuilder") as tub, \
             mock.patch("src.builders.builder.IGBuilder") as igb:
            tub.return_value.build.return_value = []
            igb.return_value.build.return_value = {}
            Builder(client).build(middleware="zenoh")
            client.import_code.assert_not_called()
            client.open_project.assert_not_called()
