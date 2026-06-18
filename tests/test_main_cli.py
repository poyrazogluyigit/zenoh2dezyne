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

    def test_amalgamation_defaults_to_source_only(self):
        from src.main import build_parser
        args = build_parser().parse_args(["-i", "examples/two-nodes"])
        self.assertEqual(args.amalgamation, "source-only")

    def test_amalgamation_rejects_invalid_choice(self):
        from src.main import build_parser
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["-i", "x", "--amalgamation", "bogus"])

    def test_amalgamation_accepts_valid_choice(self):
        from src.main import build_parser
        args = build_parser().parse_args(
            ["-i", "x", "--amalgamation", "source+all"]
        )
        self.assertEqual(args.amalgamation, "source+all")

    def test_on_missing_defaults_to_warn(self):
        from src.main import build_parser
        args = build_parser().parse_args(["-i", "examples/two-nodes"])
        self.assertEqual(args.on_missing, "warn")

    def test_on_missing_rejects_invalid_choice(self):
        from src.main import build_parser
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["-i", "x", "--on-missing", "bogus"])

    def test_on_missing_accepts_fail(self):
        from src.main import build_parser
        args = build_parser().parse_args(["-i", "x", "--on-missing", "fail"])
        self.assertEqual(args.on_missing, "fail")


if __name__ == "__main__":
    unittest.main()
