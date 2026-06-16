import re
from pathlib import Path


def detect_nodes(input_dir: Path) -> list[Path]:
    """
    Scan for .cpp files defining main() entry points.

    Returns a sorted list of Path objects for each .cpp file that defines
    int main(...) via regex matching.

    Args:
        input_dir: Root directory to scan for .cpp files

    Returns:
        Sorted list of Path objects for files containing main() definitions
    """
    pattern = re.compile(r'\bint\s+main\s*\(')
    nodes = []

    for cpp_file in sorted(input_dir.rglob('*.cpp')):
        content = cpp_file.read_text()
        if pattern.search(content):
            nodes.append(cpp_file)

    return sorted(nodes)
