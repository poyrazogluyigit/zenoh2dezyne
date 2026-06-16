# Design: quom Preprocessing Layer + Staged Build System

**Date:** 2026-06-16
**Status:** Approved (brainstorming) → ready for implementation plan

## Problem

`zenoh2dezyne` currently treats **one top-level `.cpp` file as one translation
unit** (`JoernClient.get_files` globs `cpg.file.name(".*\.cpp")`,
`unit_name_from_file` turns `A.cpp` → `A`). This breaks on real multi-file
projects:

- A node whose logic spans several files + headers gets fragmented across
  multiple Joern units.
- Shared library code (e.g. `pgm-class-lambda/netelem/netelem.cpp`) appears as
  phantom units.

Additionally the CLI has two input modes (`--project` reopen, `--input` import)
and scatters intermediates (Joern `workspace/`, stray `build/`) into the repo
root.

## Goals

1. **Agglutination preprocessing:** flatten each node's `#include` graph into a
   single self-contained `.cpp` (via [quom](https://github.com/Viatorus/quom))
   *before* Joern import, so a multi-file node analyzes as one unit.
2. **Clean, extensible build system:** the CLI takes an **input folder** and
   writes **everything** — amalgamated sources, Joern workspace, generated
   models — into a single **output folder**.

## Key facts established during brainstorming

- **quom takes a single entry file** (`quom <input> <output>`); it resolves
  local `#include`s and stitches in related source files (basename match within
  `-S` source dirs). It does **not** discover entry points — our pipeline must
  enumerate nodes and invoke quom once per node.
- **Node = a `.cpp` defining an entry point (`main()`).** Files without `main()`
  are library code that quom inlines. Detection is a lightweight regex pre-scan,
  requiring no CPG — it is genuinely a step before Joern.
- **Joern's workspace defaults to the process's working directory.** Relocating
  it needs no Joern flag — only launching the spawned `joern --server` with the
  right `cwd`. (To be verified as the first implementation task.)
- **Uniformity:** single-file nodes (today's `A.cpp`) pass through quom
  unchanged, so there is no special-casing of single- vs multi-file projects.

## Architecture (Approach B: RunContext + Pipeline)

Mirrors the existing "one package per concern" layout
(`frontend`/`builders`/`codegen`).

### 1. Output-folder contract — `RunContext`

A dataclass that is the single source of truth for all paths.

```
<out>/
├── amalgamated/     # one self-contained .cpp per node (quom output)
├── workspace/       # Joern's workspace (CPGs, projects)
└── models/          # generated .dzn files
```

Exposes: `input_dir`, `amalgamated_dir`, `workspace_dir`, `models_dir`,
`project_name` (= `basename(input_dir)`), and `mkdirs()`. No other module
computes output paths.

### 2. Node detection — `src/preprocess/`

`detect_nodes(input_dir) -> list[Path]`: recursively scan every `.cpp`, return
those whose text matches an entry-point regex (`\bint\s+main\s*\(`). Library
files (no `main()`) are excluded as nodes but remain available to quom as
include/source search dirs.

### 3. Amalgamation — `src/preprocess/`, `Amalgamator` interface

For each node:

```
quom <node.cpp> <out>/amalgamated/<node>.cpp -S <dir...> -I <dir...>
```

`-S`/`-I` = the input root **and all subdirectories**, so quom finds headers and
their related sources anywhere in the tree. Implemented as
`QuomAmalgamator(Amalgamator)` invoking quom via `subprocess` behind a single
`amalgamate(entry: Path, out_path: Path) -> None` method — swappable and
mockable. `quom` is added to `requirements.txt`.

### 4. Joern workspace relocation — `src/frontend/_connection.py`

`Connection` gains a `workspace_dir` parameter; the spawned `joern --server`
process is launched with `cwd` set so its `workspace/` lands under `<out>`. The
`--joern-server` URL is unchanged.

**Idempotency:** re-running over an existing `<out>` re-amalgamates and
re-imports. Because `importCode` will not overwrite an existing project, the
import stage deletes the project from the workspace first if present, then
imports fresh. A `--reuse-workspace` fast path is out of scope (future work).

### 5. Pipeline — `src/pipeline.py`

Explicit ordered stages, each a small class/callable over `RunContext`:

```
DetectNodes → Amalgamate → ImportToJoern → BuildGraph → Codegen → WriteModels
```

`main.py` shrinks to: parse args → build `RunContext` → `Pipeline(ctx).run()`.
`Builder` and `CodeGenerator` are reused unchanged, pointed at
`ctx.amalgamated_dir` and `ctx.models_dir`. Adding a stage = add a class + one
line.

### 6. CLI changes — `main.py`

- **Remove** `--project` and the mutually-exclusive group.
- `--input/-i` becomes **required**.
- `--output/-o` is **optional, defaults to `<cwd>/out`**.
- Keep `--middleware`, `--logging`, `--joern-server`, `--single-stepper`.
- README updated: drop two-mode explanation; document the output layout.

## Testing strategy

Real quom + real Joern are heavy external dependencies, so the pipeline must be
verifiable **without** them via a mock system.

- **Synthetic multi-file fixtures:** a small generated project tree under a test
  fixtures dir with (a) two node `.cpp` files defining `main()`, (b) a shared
  `lib/` subdir of header+source with **no** `main()`. Used to drive
  detection/amalgamation tests deterministically.
- **`FakeAmalgamator`** implementing the `Amalgamator` interface: concatenates
  the entry file + referenced library files into the output path, recording
  calls. Lets the full pipeline run end-to-end with no quom binary.
- **Fake/stubbed Joern client:** the existing codegen tests already build
  `InterconnectionGraph` fixtures without Joern; extend this so a `Pipeline` run
  can be exercised against a stub `JoernClient` returning canned query results
  for the synthetic fixture.
- **Unit tests:**
  - `detect_nodes` — with/without `main()`, nested dirs, no false positives on
    library files.
  - `QuomAmalgamator` — mock `subprocess`, assert correct quom argv (entry,
    output, `-S`/`-I` dirs).
  - `RunContext` — path computation + `mkdirs()`.
  - `Pipeline` — stage ordering, with stages mocked.
- **Gated real e2e (optional):** one end-to-end on `pgm-class-lambda` (the
  genuinely multi-file example) requiring real quom + Joern, skipped by default
  like the current Joern e2e.
- Existing codegen tests remain untouched.

## Out of scope (YAGNI)

- `--project` reopen mode (removed).
- `--reuse-workspace` incremental fast path.
- CMake-target / manifest-based node discovery.
- A dynamic stage-registry / plugin system (Approach C).
