import unittest

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.graphutils._parse_html import _clean_label, _prettify_labels


class TestParseHtml(unittest.TestCase):

    def test_clean_label_unescapes_and_splits(self):
        label = '"<put, 19<BR/>A_pub.put(&quot;example payload to A&quot;)>"'
        node_type, code = _clean_label(label)

        self.assertEqual(node_type, "put")
        self.assertEqual(code, 'A_pub.put("example payload to A")')

    def test_clean_label_case_insensitive_br(self):
        label = '<METHOD, 15<br/>&lt;lambda&gt;0>'
        node_type, code = _clean_label(label)

        self.assertEqual(node_type, "METHOD")
        self.assertEqual(code, "<lambda>0")

    def test_prettify_labels_populates_fields(self):
        nodes = [
            (1, {"label": '<METHOD_RETURN, 15<BR/>void>'}),
            (2, {"label": '<put, 19<BR/>C_pub.put(&quot;example payload to C&quot;)>'}),
        ]

        _prettify_labels(nodes)

        self.assertEqual(nodes[0][1]["node_type"], "METHOD_RETURN")
        self.assertEqual(nodes[0][1]["code"], "void")
        self.assertEqual(nodes[1][1]["node_type"], "put")
        self.assertEqual(nodes[1][1]["code"], 'C_pub.put("example payload to C")')

    def test_prettify_labels_skips_missing_label(self):
        nodes = [
            (1, {"label": ""}),
            (2, {}),
        ]

        _prettify_labels(nodes)

        self.assertNotIn("node_type", nodes[0][1])
        self.assertNotIn("code", nodes[0][1])
        self.assertNotIn("node_type", nodes[1][1])
        self.assertNotIn("code", nodes[1][1])


if __name__ == "__main__":
    unittest.main()
