import os
import unittest
import tempfile
from pathlib import Path
from src.main import main as main_cli
from src.pipeline import Pipeline
from src.context import RunContext
from src.preprocess import Amalgamator
from src.frontend import JoernClient


@unittest.skipUnless(os.environ.get("JOERN_E2E"), "Set JOERN_E2E=1 to run real e2e tests")
class TestRealMultiFileE2E(unittest.TestCase):
    """End-to-end test on pgm-class-lambda (requires real quom + Joern)."""

    def test_pgm_class_lambda_multifile(self):
        """Verify pgm-class-lambda (genuinely multi-file) produces models."""
        input_path = Path(__file__).parent.parent / "examples" / "pgm-class-lambda"
        if not input_path.exists():
            self.skipTest(f"{input_path} does not exist")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "out"
            ctx = RunContext(input_path, output_dir)

            # Run real pipeline with real quom
            with JoernClient() as client:
                Pipeline(
                    ctx,
                    client=client,
                    amalgamator=Amalgamator(),
                    middleware="zenoh",
                ).run()

            # Verify output
            self.assertTrue(ctx.models_dir.exists(), f"Models dir not created: {ctx.models_dir}")
            dzn_files = list(ctx.models_dir.glob("*.dzn"))
            self.assertGreater(len(dzn_files), 0, "No .dzn files generated")

            # Verify amalgamated sources exist
            amalg_files = list(ctx.amalgamated_dir.glob("*.cpp"))
            self.assertGreater(len(amalg_files), 0, "No amalgamated .cpp files")

            # Verify key files (sender.cpp, receiver.cpp)
            for name in ["sender.cpp", "receiver.cpp"]:
                self.assertTrue(
                    (ctx.amalgamated_dir / name).exists(),
                    f"Expected {name} not found in amalgamated/",
                )
