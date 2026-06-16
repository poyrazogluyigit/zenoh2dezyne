import tempfile
import unittest
from pathlib import Path
from src.preprocess import detect_nodes


class TestDetectNodes(unittest.TestCase):
    def _tree(self, d):
        root = Path(d)
        (root / "sender.cpp").write_text("int main() { return 0; }\n")
        (root / "receiver.cpp").write_text("int  main (int c){return 0;}\n")
        lib = root / "netelem"
        lib.mkdir()
        (lib / "netelem.cpp").write_text("void helper() {}\n")
        (lib / "netelem.h").write_text("void helper();\n")
        return root

    def test_returns_only_main_defining_cpp(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(d)
            self.assertEqual(
                sorted(p.name for p in detect_nodes(root)),
                ["receiver.cpp", "sender.cpp"],
            )

    def test_ignores_library_and_headers(self):
        with tempfile.TemporaryDirectory() as d:
            found = {p.name for p in detect_nodes(self._tree(d))}
            self.assertNotIn("netelem.cpp", found)
            self.assertNotIn("netelem.h", found)
