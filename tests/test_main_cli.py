import unittest
from pathlib import Path


class TestCli(unittest.TestCase):
    def test_output_defaults_to_cwd_out(self):
        from src.main import build_parser
        args = build_parser().parse_args(["-i", "examples/two-nodes"])
        self.assertEqual(args.output, str(Path.cwd() / "out"))

    def test_project_flag_removed(self):
        from src.main import build_parser
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--project", "x"])

    def test_input_required(self):
        from src.main import build_parser
        with self.assertRaises(SystemExit):
            build_parser().parse_args([])


if __name__ == "__main__":
    unittest.main()
