"""Mock system for verifying multi-file paths without real quom/Joern."""
from pathlib import Path


def make_multifile_project(root: Path) -> Path:
    """Generate synthetic multi-file project tree with two nodes (alpha/beta) sharing a no-main lib/.

    Args:
        root: Root directory where the project will be created

    Returns:
        The root directory (same as input)

    Creates:
        - alpha.cpp: Entry point with main(), includes lib/util.h, calls ping()
        - beta.cpp: Entry point with main(), includes lib/util.h, calls ping()
        - lib/util.h: Header declaring ping()
        - lib/util.cpp: Implementation of ping() (no main())
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / "alpha.cpp").write_text('#include "lib/util.h"\nint main(){ping();return 0;}\n')
    (root / "beta.cpp").write_text('#include "lib/util.h"\nint main(){ping();return 0;}\n')
    lib = root / "lib"
    lib.mkdir(parents=True, exist_ok=True)
    (lib / "util.h").write_text("void ping();\n")
    (lib / "util.cpp").write_text('#include "util.h"\nvoid ping(){}\n')
    return root


class FakeAmalgamator:
    """Simulates quom by concatenating entry file with all no-main lib sources.

    Attributes:
        calls: List of (entry, out_path, search_dirs) tuples recording each amalgamate() call.
    """

    def __init__(self):
        """Initialize with empty call log."""
        self.calls = []

    def amalgamate(
        self, entry: Path, out_path: Path, search_dirs: list, mode=None, on_missing=None
    ) -> None:
        """Concatenate entry + no-main lib sources into out_path; record the call.

        Simulates quom's behavior of:
        1. Reading the entry file
        2. Finding all .cpp files in search_dirs
        3. Filtering out files containing "main"
        4. Concatenating entry + filtered libs into out_path

        Args:
            entry: Entry point file to amalgamate
            out_path: Output path for the amalgamated file
            search_dirs: List of directories to search for dependencies (as list or Path objects)
        """
        self.calls.append((entry, out_path, list(search_dirs)))
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Find all .cpp files without "main" in the search directories
        libs = []
        for d in search_dirs:
            search_path = Path(d)
            if search_path.exists():
                for cpp_file in search_path.glob("**/*.cpp"):
                    content = cpp_file.read_text()
                    if "main" not in content:
                        libs.append(cpp_file)

        # Concatenate entry + lib sources
        out_path.write_text(entry.read_text() + "".join(p.read_text() for p in libs))


class StubJoernClient:
    """Canned responses so Pipeline run needs no real Joern server.

    Provides basic interface matching JoernClient without network/subprocess calls.

    Attributes:
        imported: Tuple (path, name) from most recent import_code() call, or None.
    """

    def __init__(self, files: list = None):
        """Initialize with canned file list.

        Args:
            files: List of file names to return from get_files() (e.g., ["alpha.cpp", "beta.cpp"])
        """
        self._files = files or []
        self.imported = None

    def delete_project(self, name: str) -> None:
        """No-op delete for idempotent re-imports."""
        pass

    def import_code(self, path: str, name: str) -> None:
        """Record import call; no actual file I/O.

        Args:
            path: Input path (source directory)
            name: Project name in Joern
        """
        self.imported = (path, name)

    def get_files(self) -> list:
        """Return the canned file list.

        Returns:
            List of file names provided at __init__
        """
        return self._files

    def close(self) -> None:
        """No-op close for context manager compatibility."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *_):
        """Context manager exit."""
        self.close()
