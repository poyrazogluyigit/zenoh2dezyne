import subprocess
from pathlib import Path

class Amalgamator():
    """Amalgamator using quom for C++ preprocessing and inlining."""

    def amalgamate(
        self, entry: Path, out_path: Path, search_dirs: list[Path]
    ) -> None:
        """
        Amalgamate a source file using quom.

        Args:
            entry: Entry point file to amalgamate
            out_path: Output path for the amalgamated file
            search_dirs: List of directories to search for dependencies
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)
        argv = ["quom", str(entry), str(out_path)]
        for d in search_dirs:
            argv += ["-I", str(d), "-S", str(d)]
        subprocess.run(argv, check=True)
