import unittest
from unittest import mock
from pathlib import Path
from src.pipeline import Pipeline, STAGES, _detect, _amalgamate, _import, _build, _codegen, _write
from src.context import RunContext


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
        self.assertFalse(p.single_stepper)
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


if __name__ == "__main__":
    unittest.main()
