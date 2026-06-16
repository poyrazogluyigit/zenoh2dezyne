"""Tests for Connection workspace relocation and JoernClient delete_project."""
import unittest
from pathlib import Path
from unittest import mock
from src.frontend._connection import Connection
from src.frontend.client import JoernClient


class TestConnectionWorkspace(unittest.TestCase):
    @mock.patch("src.frontend._connection.Connection.start")
    def test_workspace_dir_is_stored(self, _start):
        """workspace_dir parameter should be stored as a Path."""
        c = Connection("http://localhost:8080", workspace_dir=Path("/tmp/out/workspace"))
        self.assertEqual(c.workspace_dir, Path("/tmp/out/workspace"))

    @mock.patch("src.frontend._connection.Connection.start")
    def test_workspace_dir_none_stored(self, _start):
        """When workspace_dir is None, it should be stored as None."""
        c = Connection("http://localhost:8080", workspace_dir=None)
        self.assertIsNone(c.workspace_dir)

    @mock.patch("src.frontend._connection.Connection.start")
    def test_workspace_dir_default_none(self, _start):
        """When workspace_dir is not provided, it should be None."""
        c = Connection("http://localhost:8080")
        self.assertIsNone(c.workspace_dir)



class TestConnectionStartWithWorkspace(unittest.TestCase):
    @mock.patch("src.frontend._connection.Popen")
    @mock.patch("src.frontend._connection.requests.Session")
    def test_start_includes_workspace_flag(self, mock_session, mock_popen):
        """The start() method should include --workspace flag in argv."""
        mock_proc = mock.Mock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        mock_session_instance = mock.Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock.Mock()

        c = Connection.__new__(Connection)
        c.joern_server = "http://localhost:8080"
        c.workspace_dir = Path("/tmp/out/workspace")
        c.session = mock_session_instance
        c.proc = None

        c.start()

        # Verify that Popen was called with --workspace flag
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        self.assertIn("--workspace", call_args)
        self.assertIn("/tmp/out/workspace", call_args)

    @mock.patch("src.frontend._connection.Popen")
    @mock.patch("src.frontend._connection.requests.Session")
    def test_start_no_workspace_flag_when_none(self, mock_session, mock_popen):
        """The start() method should not include --workspace flag when workspace_dir is None."""
        mock_proc = mock.Mock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        mock_session_instance = mock.Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock.Mock()

        c = Connection.__new__(Connection)
        c.joern_server = "http://localhost:8080"
        c.workspace_dir = None
        c.session = mock_session_instance
        c.proc = None

        c.start()

        # Verify that Popen was called without --workspace flag
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        self.assertNotIn("--workspace", call_args)


class TestJoernClientWorkspace(unittest.TestCase):
    @mock.patch("src.frontend._connection.Connection.start")
    def test_joern_client_passes_workspace_dir_to_connection(self, _start):
        """JoernClient.__init__ should pass workspace_dir to Connection."""
        client = JoernClient("http://localhost:8080", workspace_dir=Path("/tmp/out/workspace"))
        self.assertEqual(client._connection.workspace_dir, Path("/tmp/out/workspace"))

    @mock.patch("src.frontend._connection.Connection.start")
    def test_joern_client_workspace_dir_none(self, _start):
        """JoernClient with workspace_dir=None should result in workspace_dir=None."""
        client = JoernClient("http://localhost:8080", workspace_dir=None)
        self.assertIsNone(client._connection.workspace_dir)

    @mock.patch("src.frontend._connection.Connection.start")
    def test_joern_client_default_workspace_dir(self, _start):
        """JoernClient with no workspace_dir should result in workspace_dir=None."""
        client = JoernClient("http://localhost:8080")
        self.assertIsNone(client._connection.workspace_dir)


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
