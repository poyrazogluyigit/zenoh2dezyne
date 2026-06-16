import tempfile
import unittest
from pathlib import Path
from unittest import mock
from src.preprocess import QuomAmalgamator


class TestQuomAmalgamator(unittest.TestCase):
    @mock.patch("src.preprocess._amalgamate.subprocess.run")
    def test_invokes_quom_with_search_dirs(self, run):
        run.return_value = mock.Mock(returncode=0)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "amalgamated" / "sender.cpp"
            QuomAmalgamator().amalgamate(
                entry=Path("/in/sender.cpp"),
                out_path=out_path,
                search_dirs=[Path("/in"), Path("/in/netelem")],
            )
            argv = run.call_args.args[0]
            self.assertEqual(argv[:3], ["quom", "/in/sender.cpp", str(out_path)])
            self.assertIn("-I", argv)
            self.assertIn("/in/netelem", argv)
            self.assertIn("-S", argv)
            self.assertTrue(run.call_args.kwargs.get("check"))
