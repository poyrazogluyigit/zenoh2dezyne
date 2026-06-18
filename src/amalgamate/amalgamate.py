"""Manual C++ amalgamation.

Read an input directory. For each translation unit with an entry point
(main()), create an amalgamated version based on a chosen mode:
    - source-only:    inline only files within the source directory
    - source+project: inline resolvable "..." includes; leave <...> alone
    - source+all:     inline any resolvable include; leave true system alone
"""

import logging
import re
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

_INCLUDE = re.compile(r'^\s*#\s*include\s*(?:"([^"]+)"|<([^>]+)>)')
_MAIN = re.compile(r'\bint\s+main\s*\(')
# A class/struct declaration or forward declaration (excludes `enum class`):
#   class Foo;  | struct Bar {  | class Baz final : public Qux
_CLASS_DECL = re.compile(r'(?<!enum )\b(?:class|struct)\s+(\w+)(?:\s+final)?\s*[:{;]')


def detect_nodes(input_dir: Path) -> list[Path]:
    """Return a sorted list of .cpp files under `input_dir` that define main()."""
    return sorted(
        cpp
        for cpp in input_dir.rglob("*.cpp")
        if _MAIN.search(cpp.read_text())
    )


class AmalgamationMode(Enum):
    SOURCE_ONLY = "source-only"
    SOURCE_PROJECT = "source+project"
    SOURCE_ALL = "source+all"


class OnMissing(Enum):
    FAIL = "fail"
    WARN = "warn"


def _comment_mask(line: str, in_block: bool) -> tuple[list[bool], bool]:
    """Mark characters that fall inside a C/C++ comment.

    Tracks string and char literals so that ``/*``, ``*/`` or ``//`` appearing
    inside a literal do not start or end a comment. `in_block` carries the
    open-block-comment state in from the previous line; the returned bool is
    the state after this line.
    """
    mask = [False] * len(line)
    i, n = 0, len(line)
    in_string: str | None = None
    while i < n:
        c = line[i]
        two = line[i : i + 2]
        if in_block:
            mask[i] = True
            if two == "*/":
                mask[i + 1] = True
                in_block = False
                i += 2
                continue
            i += 1
        elif in_string is not None:
            if c == "\\":
                i += 2  # skip escaped char
                continue
            if c == in_string:
                in_string = None
            i += 1
        elif two == "//":
            for j in range(i, n):
                mask[j] = True
            break
        elif two == "/*":
            mask[i] = mask[i + 1] = True
            in_block = True
            i += 2
        elif c in ('"', "'"):
            in_string = c
            i += 1
        else:
            i += 1
    return mask, in_block


def _resolve(name: str, search_dirs: list[Path]) -> Path | None:
    """Return the first existing path for `name` across `search_dirs`."""
    for d in search_dirs:
        candidate = d / name
        if candidate.is_file():
            return candidate
    return None


def _declared_classes(text: str) -> set[str]:
    """Names of classes/structs declared (or forward-declared) in `text`."""
    return set(_CLASS_DECL.findall(text))


def _definer_pattern(classes: set[str]) -> re.Pattern[str] | None:
    """Regex matching an out-of-line member definition ``Class::`` for any of
    `classes`, i.e. the translation unit that *defines* that class's members."""
    if not classes:
        return None
    alt = "|".join(re.escape(c) for c in classes)
    return re.compile(rf'\b(?:{alt})::')


class Amalgamator:
    """Inlines a translation unit's dependencies per a chosen mode."""

    def amalgamate(
        self,
        entry: Path,
        out_path: Path,
        search_dirs: list[Path],
        mode: AmalgamationMode,
        on_missing: OnMissing = OnMissing.WARN,
    ) -> None:
        source_dir = search_dirs[0]
        visited: set[Path] = {entry.resolve()}
        parts = [self._inline(entry, search_dirs, source_dir, mode, on_missing, visited)]

        # Linker phase. A .cpp belongs to this executable if it *defines* the
        # members of a class *declared* by a header we have already inlined --
        # regardless of the file's name or location. Inlining a definer may pull
        # in further headers (new declarations), so repeat until nothing is added.
        candidates = [
            (cpp, text)
            for cpp in sorted(source_dir.rglob("*.cpp"))
            if cpp.resolve() not in visited and not _MAIN.search(text := cpp.read_text())
        ]
        while True:
            pattern = _definer_pattern(_declared_classes("".join(parts)))
            added = False
            if pattern is not None:
                for cpp, text in candidates:
                    key = cpp.resolve()
                    if key in visited or not pattern.search(text):
                        continue
                    visited.add(key)
                    parts.append(self._inline(cpp, search_dirs, source_dir, mode, on_missing, visited))
                    added = True
            if not added:
                break

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(parts))

    def _inline(
        self,
        file: Path,
        search_dirs: list[Path],
        source_dir: Path,
        mode: AmalgamationMode,
        on_missing: OnMissing,
        visited: set[Path],
    ) -> str:
        out_lines: list[str] = []
        in_block = False
        for line in file.read_text().splitlines(keepends=True):
            mask, in_block = _comment_mask(line, in_block)
            m = _INCLUDE.match(line)
            if m and not mask[m.start()]:
                name = m.group(1) or m.group(2)
                is_system = m.group(2) is not None
                resolved = _resolve(name, search_dirs)
                if resolved is not None and self._should_inline(resolved, is_system, source_dir, mode):
                    key = resolved.resolve()
                    if key in visited:
                        continue  # already inlined; include-guard equivalent
                    visited.add(key)
                    out_lines.append(
                        self._inline(
                            resolved, search_dirs, source_dir, mode, on_missing, visited
                        )
                    )
                    continue
                if resolved is None and not is_system:
                    self._handle_missing(name, file, on_missing)
            out_lines.append(line)
        return "".join(out_lines)

    def _should_inline(
        self,
        resolved: Path,
        is_system: bool,
        source_dir: Path,
        mode: AmalgamationMode,
    ) -> bool:
        if mode is AmalgamationMode.SOURCE_ONLY:
            return resolved.is_relative_to(source_dir)
        if mode is AmalgamationMode.SOURCE_PROJECT:
            return not is_system
        return True  # SOURCE_ALL: any resolvable include

    def _handle_missing(self, name: str, includer: Path, on_missing: OnMissing) -> None:
        msg = f'could not resolve #include "{name}" from {includer}'
        if on_missing is OnMissing.FAIL:
            logger.error(msg)
            raise FileNotFoundError(msg)
        logger.warning(msg)
