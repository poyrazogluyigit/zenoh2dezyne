"""Naming/mangling helpers for translating Zenoh identifiers into Dezyne identifiers."""
import os


def mangle_topic(topic: str) -> str:
    """Translate a Zenoh key expression into a valid Dezyne event identifier.

    Zenoh topics use '/' as a separator (e.g. ``basic/B/A``); Dezyne identifiers
    cannot contain '/' so we replace each one with '_'.
    """
    return topic.replace("/", "_")


def unit_name_from_file(file_name: str) -> str:
    """Derive a unit identifier from a TranslationUnit.file_name.

    ``foo/bar/A.cpp`` -> ``A``. The result is used as the per-unit interface
    suffix (``IA``), component name suffix (``CA``), port prefix (``A_top``)
    and output filename (``A.dzn``).
    """
    return os.path.splitext(os.path.basename(file_name))[0]
