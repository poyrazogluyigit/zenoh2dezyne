"""Tests for Connection workspace relocation and JoernClient delete_project."""
import unittest
from pathlib import Path
from unittest import mock
from src.frontend._connection import Connection
from src.frontend.client import JoernClient


class TestConnectionWorkspace(unittest.TestCase):
    @mock.patch("src.frontend._connection.Connection.start")
    def test_workspace_dir_sets_cwd(self, _start):
        """workspace_dir parameter should set cwd to its parent directory."""
        c = Connection("http://localhost:8080", workspace_dir=Path("/tmp/out/workspace"))
        self.assertEqual(c.cwd, Path("/tmp/out"))

    @mock.patch("src.frontend._connection.Connection.start")
    def test_workspace_dir_none_sets_cwd_none(self, _start):
        """When workspace_dir is None, cwd should be None."""
        c = Connection("http://localhost:8080", workspace_dir=None)
        self.assertIsNone(c.cwd)

    @mock.patch("src.frontend._connection.Connection.start")
    def test_workspace_dir_default_sets_cwd_none(self, _start):
        """When workspace_dir is not provided, cwd should be None."""
        c = Connection("http://localhost:8080")
        self.assertIsNone(c.cwd)



class TestConnectionStartWithCwd(unittest.TestCase):
    @mock.patch("src.frontend._connection.Popen")
    @mock.patch("src.frontend._connection.requests.Session")
    def test_start_passes_cwd_to_popen(self, mock_session, mock_popen):
        """The start() method should pass cwd parameter to Popen."""
        mock_proc = mock.Mock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        mock_session_instance = mock.Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.get.return_value = mock.Mock()

        c = Connection.__new__(Connection)
        c.joern_server = "http://localhost:8080"
        c.cwd = Path("/tmp/out")
        c.session = mock_session_instance
        c.proc = None

        c.start()

        # Verify that Popen was called with cwd parameter
        mock_popen.assert_called_once()
        call_kwargs = mock_popen.call_args[1]
        self.assertEqual(call_kwargs.get("cwd"), Path("/tmp/out"))

    @mock.patch("src.frontend._connection.Popen")
    @mock.patch("src.frontend._connection.requests.Session")
    def test_start_passes_none_cwd_to_popen(self, mock_session, mock_popen):
        """The start() method should pass cwd=None to Popen when cwd is None."""
        mock_proc = mock.Mock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        mock_session_instance = mock.Mock()
        mock_session.return_value = mock.Mock()
        mock_session_instance.get.return_value = mock.Mock()

        c = Connection.__new__(Connection)
        c.joern_server = "http://localhost:8080"
        c.cwd = None
        c.session = mock_session_instance
        c.proc = None

        c.start()

        # Verify that Popen was called with cwd=None
        mock_popen.assert_called_once()
        call_kwargs = mock_popen.call_args[1]
        self.assertIsNone(call_kwargs.get("cwd"))


class TestJoernClientWorkspace(unittest.TestCase):
    @mock.patch("src.frontend._connection.Connection.start")
    def test_joern_client_passes_workspace_dir_to_connection(self, _start):
        """JoernClient.__init__ should pass workspace_dir to Connection."""
        client = JoernClient("http://localhost:8080", workspace_dir=Path("/tmp/out/workspace"))
        self.assertEqual(client._connection.cwd, Path("/tmp/out"))

    @mock.patch("src.frontend._connection.Connection.start")
    def test_joern_client_workspace_dir_none(self, _start):
        """JoernClient with workspace_dir=None should result in cwd=None."""
        client = JoernClient("http://localhost:8080", workspace_dir=None)
        self.assertIsNone(client._connection.cwd)

    @mock.patch("src.frontend._connection.Connection.start")
    def test_joern_client_default_workspace_dir(self, _start):
        """JoernClient with no workspace_dir should result in cwd=None."""
        client = JoernClient("http://localhost:8080")
        self.assertIsNone(client._connection.cwd)


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
