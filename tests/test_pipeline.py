import unittest
from unittest import mock
from pathlib import Path
import tempfile
from src.pipeline import Pipeline, STAGES, _detect, _amalgamate, _import, _build, _codegen, _write
from src.context import RunContext
from tests.fixtures import make_multifile_project, FakeAmalgamator, StubJoernClient
from src.builders import InterconnectionGraph


class TestPipelineOrder(unittest.TestCase):
    def test_runs_stages_in_order(self):
        ctx = RunContext(Path("/in/proj"), Path("/out"))
        p = Pipeline(ctx, client=mock.Mock(), amalgamator=mock.Mock())
        calls = []

        # Create mock stages with proper __name__ attribute
        stages = []
        for i in range(len(STAGES)):
            m = mock.Mock(side_effect=lambda _p, n=i: calls.append(n))
            m.__name__ = f"stage_{i}"
            stages.append(m)

        with mock.patch("src.pipeline.STAGES", stages):
            p.run()
        self.assertEqual(calls, list(range(len(STAGES))))

    def test_stages_is_correct_sequence(self):
        """Verify the STAGES list has the correct functions in order."""
        self.assertEqual(len(STAGES), 6)
        self.assertEqual(STAGES[0].__name__, "_detect")
        self.assertEqual(STAGES[1].__name__, "_amalgamate")
        self.assertEqual(STAGES[2].__name__, "_import")
        self.assertEqual(STAGES[3].__name__, "_build")
        self.assertEqual(STAGES[4].__name__, "_codegen")
        self.assertEqual(STAGES[5].__name__, "_write")

    def test_pipeline_initializes_with_defaults(self):
        """Verify Pipeline dataclass initializes with proper defaults."""
        ctx = RunContext(Path("/in"), Path("/out"))
        p = Pipeline(ctx, client=mock.Mock(), amalgamator=mock.Mock())
        self.assertEqual(p.middleware, "zenoh")
        self.assertEqual(p.nodes, [])
        self.assertIsNone(p.graph)
        self.assertIsNone(p.codegen)

    def test_detect_populates_nodes(self):
        """Verify _detect stage populates p.nodes."""
        ctx = RunContext(Path("/in"), Path("/out"))
        p = Pipeline(ctx, client=mock.Mock(), amalgamator=mock.Mock())

        mock_nodes = [Path("a.cpp"), Path("b.cpp")]
        with mock.patch("src.pipeline.detect_nodes", return_value=mock_nodes):
            with mock.patch.object(ctx, "mkdirs"):
                _detect(p)

        self.assertEqual(p.nodes, mock_nodes)

    def test_endtoend_multifile_with_fakes(self):
        """End-to-end pipeline test with synthetic project and fakes.

        Verifies:
        - Detect finds alpha.cpp and beta.cpp (no util.cpp)
        - Amalgamate merges util lib into each node
        - Import is called with amalgamated dir
        - Build uses mocked Builder
        - Codegen and write produce output
        """
        with tempfile.TemporaryDirectory() as d:
            root = make_multifile_project(Path(d) / "proj")
            ctx = RunContext(root, Path(d) / "out")
            client = StubJoernClient(files=["alpha.cpp", "beta.cpp"])

            # Run pipeline with mocked Builder
            with mock.patch("src.pipeline.Builder") as builder_mock:
                # Create a mock graph for codegen to use
                graph_mock = mock.Mock()
                builder_mock.return_value.build.return_value = graph_mock

                # Create a mock codegen to avoid real code generation
                with mock.patch("src.pipeline.CodeGenerator") as codegen_mock:
                    codegen_instance = mock.Mock()
                    codegen_mock.return_value = codegen_instance

                    Pipeline(ctx, client=client, amalgamator=FakeAmalgamator()).run()

                    # Verify Builder.build() was called
                    builder_mock.assert_called_once()
                    # Verify CodeGenerator was instantiated with models_dir
                    codegen_mock.assert_called_once_with(str(ctx.models_dir))
                    # Verify codegen.generate() was called
                    codegen_instance.generate.assert_called_once()
                    # Verify codegen.printToOutput() was called
                    codegen_instance.printToOutput.assert_called_once()

            # Verify amalgamated files exist and contain merged content
            alpha_amalg = ctx.amalgamated_dir / "alpha.cpp"
            beta_amalg = ctx.amalgamated_dir / "beta.cpp"

            self.assertTrue(alpha_amalg.exists(), "alpha.cpp should be amalgamated")
            self.assertTrue(beta_amalg.exists(), "beta.cpp should be amalgamated")

            alpha_content = alpha_amalg.read_text()
            beta_content = beta_amalg.read_text()

            # Verify util.cpp content was inlined (ping() appears in both)
            self.assertIn("ping()", alpha_content, "alpha.cpp should contain inlined lib")
            self.assertIn("ping()", beta_content, "beta.cpp should contain inlined lib")

            # Verify lib/util.cpp did NOT become its own node (only alpha/beta are entry points)
            util_amalg = ctx.amalgamated_dir / "util.cpp"
            self.assertFalse(util_amalg.exists(), "util.cpp should not be a standalone node")

            # Verify models dir was created
            self.assertTrue(ctx.models_dir.exists(), "models directory should be created")

            # Verify Joern client was called (imported is set by import_code)
            self.assertIsNotNone(client.imported, "Client should have recorded import_code call")
            path, name = client.imported
            self.assertEqual(name, ctx.project_name, f"Project name should be '{ctx.project_name}'")


if __name__ == "__main__":
    unittest.main()
