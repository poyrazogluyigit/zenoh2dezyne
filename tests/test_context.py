import unittest
import tempfile
from pathlib import Path
from src.context import RunContext


class TestRunContext(unittest.TestCase):
    def test_paths_derive_from_output(self):
        ctx = RunContext(input_dir=Path("/x/basic-example"), output_dir=Path("/tmp/out"))
        self.assertEqual(ctx.project_name, "basic-example")
        self.assertEqual(ctx.amalgamated_dir, Path("/tmp/out/amalgamated"))
        self.assertEqual(ctx.models_dir, Path("/tmp/out/models"))

    def test_mkdirs_creates_all(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = RunContext(input_dir=Path(d), output_dir=Path(d) / "out")
            ctx.mkdirs()
            for p in (ctx.amalgamated_dir, ctx.models_dir):
                self.assertTrue(p.is_dir())
