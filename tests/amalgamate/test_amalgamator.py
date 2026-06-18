import tempfile
import unittest
from pathlib import Path

from src.amalgamate import (
    Amalgamator,
    AmalgamationMode,
    OnMissing,
    detect_nodes,
)


class TestDetectNodes(unittest.TestCase):
    def test_finds_entry_points_and_excludes_non_main(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sender.cpp").write_text("int main() { return 0; }\n")
            (root / "receiver.cpp").write_text("int  main (int c){return 0;}\n")
            lib = root / "netelem"
            lib.mkdir()
            (lib / "netelem.cpp").write_text("void helper() {}\n")
            (lib / "netelem.h").write_text("void helper();\n")

            names = sorted(p.name for p in detect_nodes(root))
            self.assertEqual(names, ["receiver.cpp", "sender.cpp"])


class TestSourceProject(unittest.TestCase):
    def test_inlines_project_header_drops_its_include_keeps_system(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "util.h").write_text("int util() { return 7; }\n")
            (src / "main.cpp").write_text(
                "#include <iostream>\n"
                '#include "util.h"\n'
                "int main() { return util(); }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            text = out.read_text()
            self.assertIn("int util()", text)
            self.assertNotIn('#include "util.h"', text)
            self.assertIn("#include <iostream>", text)


class TestRecursionAndGuards(unittest.TestCase):
    def test_inlines_transitively(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "b.h").write_text("int b() { return 2; }\n")
            (src / "a.h").write_text('#include "b.h"\nint a() { return b(); }\n')
            (src / "main.cpp").write_text('#include "a.h"\nint main() { return a(); }\n')
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            text = out.read_text()
            self.assertIn("int a()", text)
            self.assertIn("int b()", text)

    def test_duplicate_header_inlined_once(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "b.h").write_text("int b() { return 2; }\n")
            (src / "a.h").write_text('#include "b.h"\nint a() { return b(); }\n')
            (src / "main.cpp").write_text(
                '#include "a.h"\n#include "b.h"\nint main() { return a() + b(); }\n'
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            self.assertEqual(out.read_text().count("int b()"), 1)

    def test_circular_includes_terminate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "a.h").write_text('#include "b.h"\nint a();\n')
            (src / "b.h").write_text('#include "a.h"\nint b();\n')
            (src / "main.cpp").write_text('#include "a.h"\nint main() { return 0; }\n')
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            text = out.read_text()
            self.assertEqual(text.count("int a();"), 1)
            self.assertEqual(text.count("int b();"), 1)


class TestSourceAll(unittest.TestCase):
    def test_inlines_resolvable_angle_include(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "sys.h").write_text("int sys() { return 9; }\n")
            (src / "main.cpp").write_text(
                "#include <sys.h>\nint main() { return sys(); }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_ALL,
            )

            text = out.read_text()
            self.assertIn("int sys()", text)
            self.assertNotIn("#include <sys.h>", text)

    def test_leaves_unresolvable_angle_include_alone(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "main.cpp").write_text(
                "#include <iostream>\nint main() { return 0; }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_ALL,
            )

            self.assertIn("#include <iostream>", out.read_text())


class TestOnMissing(unittest.TestCase):
    def _project_with_missing_include(self, root):
        src = root / "src"
        src.mkdir()
        (src / "main.cpp").write_text(
            '#include "missing.h"\nint main() { return 0; }\n'
        )
        return src

    def test_warn_keeps_line_and_logs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self._project_with_missing_include(root)
            out = root / "out" / "main.cpp"

            with self.assertLogs("src.amalgamate.amalgamate", level="WARNING"):
                Amalgamator().amalgamate(
                    entry=src / "main.cpp",
                    out_path=out,
                    search_dirs=[src],
                    mode=AmalgamationMode.SOURCE_PROJECT,
                    on_missing=OnMissing.WARN,
                )

            self.assertIn('#include "missing.h"', out.read_text())

    def test_fail_raises(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = self._project_with_missing_include(root)
            out = root / "out" / "main.cpp"

            with self.assertRaises(FileNotFoundError):
                Amalgamator().amalgamate(
                    entry=src / "main.cpp",
                    out_path=out,
                    search_dirs=[src],
                    mode=AmalgamationMode.SOURCE_PROJECT,
                    on_missing=OnMissing.FAIL,
                )


class TestCommentTracking(unittest.TestCase):
    def test_include_inside_block_comment_not_inlined(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "old.h").write_text("int OLD() { return 0; }\n")
            (src / "real.h").write_text("int REAL() { return 1; }\n")
            (src / "main.cpp").write_text(
                "/* legacy:\n"
                '#include "old.h"\n'
                "*/\n"
                '#include "real.h"\n'
                "int main() { return REAL(); }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            text = out.read_text()
            self.assertIn("int REAL()", text)            # real include inlined
            self.assertNotIn("int OLD()", text)          # commented include skipped
            self.assertIn('#include "old.h"', text)      # comment preserved verbatim
            self.assertNotIn('#include "real.h"', text)  # real include consumed

    def test_single_line_block_comment_include_not_inlined(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "old.h").write_text("int OLD() { return 0; }\n")
            (src / "main.cpp").write_text(
                '/* #include "old.h" */\n'
                "int main() { return 0; }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            self.assertNotIn("int OLD()", out.read_text())

    def test_slash_star_in_string_does_not_open_comment(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            (src / "real.h").write_text("int REAL() { return 1; }\n")
            (src / "main.cpp").write_text(
                'const char* s = "/*";\n'
                '#include "real.h"\n'
                "int main() { return REAL(); }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src],
                mode=AmalgamationMode.SOURCE_PROJECT,
            )

            # The "/*" lives in a string, so the real include below must still inline.
            self.assertIn("int REAL()", out.read_text())


class TestSourceOnly(unittest.TestCase):
    def test_inlines_sibling_under_source_dir_but_not_distant_header(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            far = root / "vendor"
            far.mkdir()
            (src / "local.h").write_text("int local() { return 1; }\n")
            (far / "remote.h").write_text("int remote() { return 2; }\n")
            (src / "main.cpp").write_text(
                '#include "local.h"\n'
                '#include "remote.h"\n'
                "int main() { return local() + remote(); }\n"
            )
            out = root / "out" / "main.cpp"

            Amalgamator().amalgamate(
                entry=src / "main.cpp",
                out_path=out,
                search_dirs=[src, far],
                mode=AmalgamationMode.SOURCE_ONLY,
            )

            text = out.read_text()
            self.assertIn("int local()", text)
            self.assertNotIn('#include "local.h"', text)
            self.assertIn('#include "remote.h"', text)
            self.assertNotIn("int remote()", text)
