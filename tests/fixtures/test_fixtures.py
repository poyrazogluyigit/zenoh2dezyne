"""Verify fixtures work: make_multifile_project, FakeAmalgamator, StubJoernClient."""
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import make_multifile_project, FakeAmalgamator, StubJoernClient


class TestMakeMultifileProject(unittest.TestCase):
    """Verify make_multifile_project() creates the correct file structure."""

    def test_creates_all_files(self):
        """Verify all expected files are created."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            self.assertTrue((root / "alpha.cpp").exists())
            self.assertTrue((root / "beta.cpp").exists())
            self.assertTrue((root / "lib" / "util.h").exists())
            self.assertTrue((root / "lib" / "util.cpp").exists())

    def test_alpha_has_main(self):
        """Verify alpha.cpp contains main() entry point."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            content = (root / "alpha.cpp").read_text()
            self.assertIn("int main()", content)
            self.assertIn("ping()", content)
            self.assertIn("#include", content)

    def test_beta_has_main(self):
        """Verify beta.cpp contains main() entry point."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            content = (root / "beta.cpp").read_text()
            self.assertIn("int main()", content)
            self.assertIn("ping()", content)
            self.assertIn("#include", content)

    def test_lib_util_h_no_main(self):
        """Verify lib/util.h has no main()."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            content = (root / "lib" / "util.h").read_text()
            self.assertNotIn("main", content)
            self.assertIn("void ping()", content)

    def test_lib_util_cpp_no_main(self):
        """Verify lib/util.cpp has no main()."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            content = (root / "lib" / "util.cpp").read_text()
            self.assertNotIn("main", content)
            self.assertIn("void ping(){}", content)

    def test_returns_root_directory(self):
        """Verify function returns the root directory."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            self.assertEqual(root, Path(d) / "proj")


class TestFakeAmalgamator(unittest.TestCase):
    """Verify FakeAmalgamator simulates quom behavior."""

    def test_creates_output_file(self):
        """Verify amalgamate() creates the output file."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            amalg = FakeAmalgamator()
            out = Path(d) / "out"
            amalg.amalgamate(root / "alpha.cpp", out / "alpha.cpp", [root / "lib"])
            self.assertTrue((out / "alpha.cpp").exists())

    def test_concatenates_entry_and_libs(self):
        """Verify output contains entry file + lib sources without main."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            amalg = FakeAmalgamator()
            out = Path(d) / "out"
            amalg.amalgamate(root / "alpha.cpp", out / "alpha.cpp", [root / "lib"])
            content = (out / "alpha.cpp").read_text()

            # Should have entry
            self.assertIn("int main()", content)
            # Should have lib
            self.assertIn("void ping(){}", content)

    def test_excludes_files_with_main(self):
        """Verify only lib files without main are included."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            amalg = FakeAmalgamator()
            out = Path(d) / "out"

            # Amalgamate alpha into lib dir (which has util.cpp but not beta)
            amalg.amalgamate(root / "alpha.cpp", out / "alpha.cpp", [root / "lib"])
            content = (out / "alpha.cpp").read_text()

            # beta.cpp should NOT be in there (it's not in lib/)
            self.assertNotIn("beta", content)

    def test_records_call(self):
        """Verify calls list tracks each amalgamate() invocation."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            amalg = FakeAmalgamator()
            out = Path(d) / "out"

            self.assertEqual(len(amalg.calls), 0)
            amalg.amalgamate(root / "alpha.cpp", out / "alpha.cpp", [root / "lib"])
            self.assertEqual(len(amalg.calls), 1)

            entry, out_path, search_dirs = amalg.calls[0]
            self.assertEqual(entry, root / "alpha.cpp")
            self.assertEqual(out_path, out / "alpha.cpp")
            self.assertEqual(search_dirs, [root / "lib"])

    def test_multiple_calls(self):
        """Verify multiple amalgamate() calls are all recorded."""
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            amalg = FakeAmalgamator()
            out = Path(d) / "out"

            amalg.amalgamate(root / "alpha.cpp", out / "alpha.cpp", [root / "lib"])
            amalg.amalgamate(root / "beta.cpp", out / "beta.cpp", [root / "lib"])

            self.assertEqual(len(amalg.calls), 2)
            self.assertEqual(amalg.calls[0][0], root / "alpha.cpp")
            self.assertEqual(amalg.calls[1][0], root / "beta.cpp")


class TestStubJoernClient(unittest.TestCase):
    """Verify StubJoernClient provides canned Joern responses."""

    def test_get_files_returns_list(self):
        """Verify get_files() returns the initialized file list."""
        client = StubJoernClient(files=["alpha.cpp", "beta.cpp"])
        self.assertEqual(client.get_files(), ["alpha.cpp", "beta.cpp"])

    def test_get_files_empty_by_default(self):
        """Verify get_files() returns empty list if not provided."""
        client = StubJoernClient()
        self.assertEqual(client.get_files(), [])

    def test_delete_project_no_op(self):
        """Verify delete_project() is a no-op."""
        client = StubJoernClient()
        # Should not raise
        client.delete_project("myproject")

    def test_import_code_records_call(self):
        """Verify import_code() records the path and name."""
        client = StubJoernClient()
        self.assertIsNone(client.imported)
        client.import_code("/path/to/code", "myproject")
        self.assertEqual(client.imported, ("/path/to/code", "myproject"))

    def test_import_code_overwrites_previous(self):
        """Verify second import_code() overwrites the first."""
        client = StubJoernClient()
        client.import_code("/path1", "proj1")
        client.import_code("/path2", "proj2")
        self.assertEqual(client.imported, ("/path2", "proj2"))

    def test_context_manager(self):
        """Verify StubJoernClient works as a context manager."""
        with StubJoernClient(files=["test.cpp"]) as client:
            self.assertEqual(client.get_files(), ["test.cpp"])

    def test_close_is_no_op(self):
        """Verify close() is a no-op."""
        client = StubJoernClient()
        # Should not raise
        client.close()


if __name__ == "__main__":
    unittest.main()
