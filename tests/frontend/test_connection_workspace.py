"""Tests for JoernClient.delete_project."""
import unittest
from unittest import mock
from src.frontend.client import JoernClient


class TestJoernClientDeleteProject(unittest.TestCase):
    @mock.patch("src.frontend._connection.Connection.start")
    @mock.patch.object(JoernClient, "_send_query")
    def test_delete_project_sends_correct_query(self, mock_send_query, _start):
        """delete_project should send a Scala delete query with the project name."""
        mock_send_query.return_value = "success"

        client = JoernClient("http://localhost:8080")
        result = client.delete_project("my_project")

        mock_send_query.assert_called_once_with('delete("my_project")')
        self.assertEqual(result, "success")

    @mock.patch("src.frontend._connection.Connection.start")
    @mock.patch.object(JoernClient, "_send_query")
    def test_delete_project_returns_raw_query_result(self, mock_send_query, _start):
        """delete_project should return the raw query result without JSON parsing."""
        mock_send_query.return_value = "Project deleted"

        client = JoernClient("http://localhost:8080")
        result = client.delete_project("test_proj")

        self.assertEqual(result, "Project deleted")


if __name__ == "__main__":
    unittest.main()
