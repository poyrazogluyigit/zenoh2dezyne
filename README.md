# Zenoh-to-Dezyne Model Translator

`zenoh2dezyne` is a static-analysis-driven translator that extracts the
publish/subscribe behaviour of a [Zenoh](https://zenoh.io/) C++ application and
emits an equivalent [Dezyne](https://gitlab.com/dezyne/dezyne) formal model.
The generated model is suitable for verification with the Dezyne toolchain.

The repository ships with several example systems for testing and benchmarking:

- [`examples/basic-example`](examples/basic-example) — three units (A/B/C) cross-publishing on three topics.
- [`examples/dining-philosophers`](examples/dining-philosophers) — naive dining-philosophers solution.
- [`examples/pgm-protocol`](examples/pgm-protocol), [`pgm-class-lambda`](examples/pgm-class-lambda) — simplifications of the PGM (Pragmatic General Multicast) protocol.
- [`examples/two-nodes`](examples/two-nodes) — minimal two-node smoke test.

In its current state, the code generator generates models for basic-example.

## Roadmap
- [ ] Re-evaluate existing examples
- [ ] Add new examples
- [ ] Append a source file aggregation step before building the translation units
    - Will likely use quom 

The examples are inspired by the [BEEM Benchmark Suite](https://github.com/plug-obp/beem-benchmark).

## Pipeline

```
  Zenoh C++ source
        │
        ▼
  ┌───────────────┐     ┌────────────────────┐
  │ Joern server  │ ──► │  src/frontend      │   Joern queries → publishers,
  │ (CPG analysis)│     │  (JoernQueryAPI)   │   subscribers, CFGs as DOT
  └───────────────┘     └────────────────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  src/builders      │   TUBuilder builds per-file
                        │  TUBuilder         │   TranslationUnits (main +
                        │  IGBuilder         │   callbacks, var/sess pubs);
                        └────────────────────┘   IGBuilder links them by topic
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  src/codegen       │   CFG → mid-IR StateMachine →
                        │  CodeGenerator     │   AST → .dzn text
                        └────────────────────┘
                                  │
                                  ▼
                        Generated Dezyne files
                        (one per unit + Network + Top + Step)
```

Each translation unit becomes one `interface I<Unit>` (with all of its threads
dispatched by a `CurrentExecutionThread` enum) and a wrapping `component
C<Unit>`. Cross-unit communication is wired through a generated `Network`
component; the whole system is assembled in `Top`.

## Requirements

- **Python 3.13+** (uses `X | Y` union annotations and the latest `dataclass` semantics).
- A running **[Joern](https://github.com/joernio/joern)** server (defaults to `http://localhost:8080`).
- Python dependencies: `networkx`, `requests`, `pyparsing` (transitively pulled in by the included `.venv`, or install manually).

## Installation

```bash
git clone https://github.com/<you>/zenoh2dezyne.git
cd zenoh2dezyne
python3.13 -m venv .venv
source .venv/bin/activate
pip install networkx requests pyparsing
```

Start a Joern server in a separate terminal:

```bash
joern --server
```

Joern persists projects in its workspace across runs, so once a source tree has
been imported under a given project name it can be re-opened by name in later
invocations — see the two CLI modes below.

## Usage

```bash
python -m src.main (--project NAME | --input PATH) \
    --output <dir> \
    --joern-server <url> \
    --logging <LEVEL> \
    [--single-stepper]
```

Exactly one of `--project` or `--input` is required:

- **`--project NAME`** opens an existing Joern project by name. Use this when
  the source has already been imported in a previous run.
- **`--input PATH`** runs `importCode` on the source directory at `PATH`. The
  project name is taken from the directory's basename, so
  `--input examples/basic-example` registers the project as `basic-example`.
  A line `creating project with <name>` is printed when this happens.

| Flag | Default | Description |
|---|---|---|
| `-p, --project` | — | Open an existing Joern project by name. |
| `-i, --input` | — | Import a source directory; project name = basename. |
| `-o, --output` | `generate` | Directory to write generated `.dzn` files into. |
| `--joern-server` | `http://localhost:8080` | URL of the running Joern server. |
| `-l, --logging` | `WARNING` | Logging verbosity (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`). |
| `--single-stepper` | off | Generate one shared `Step` component instead of one per unit. |

### End-to-end example

First run — import the source:

```bash
python -m src.main --input examples/basic-example -o /tmp/basic-example-models \
    --joern-server http://localhost:8080
# prints: creating project with basic-example
```

Subsequent runs against the same project:

```bash
python -m src.main --project basic-example -o /tmp/basic-example-models \
    --joern-server http://localhost:8080
```

Produces, in `/tmp/basic-example-models/`:

```
A.dzn        B.dzn        C.dzn        Network.dzn        Top.dzn        Step.dzn
```

## Generated model shape

### Per-unit interface (`<Unit>.dzn`)

- One interface `I<Unit>` declaring:
  - `out void <mangled_topic>();` for every published topic.
  - `out void <thread>_branch_<src>_to_<tgt>();` for every nondeterministic transition (one per branch).
  - `in void <mangled_topic>();` for every subscribed topic.
  - `in void step();` — the stepper trigger.
- A `behavior { ... }` block with:
  - `enum CurrentExecutionThread { main, <callback names>... };` and a `thread` variable.
  - `subint State_<thread> { 1..N };` and `s_<thread>` variable per thread.
  - One `on step:` trigger that dispatches first on `thread`, then on the per-thread state variable.
  - One `on <topic>:` trigger per subscribed topic that switches execution into the corresponding callback when the unit is on `main`.
- A wrapping component `C<Unit>` that `provides I<Unit> <Unit>_top;`.

### Network (`Network.dzn`)

- Interface `INetCtl` exposing `in void kick()`.
- Component `Network`:
  - `provides INetCtl ctl;`
  - `requires I<Unit> <Unit>;` for every unit.
  - `requires IStep s<i>;` per unit (or `requires IStep s;` under `--single-stepper`).
  - `behavior` containing:
    - `on ctl.kick(): {}` boot-up handler.
    - `on <src>.<topic>(): <dst>.<topic>();` for every publisher→subscriber edge.
    - `on <unit>.<branch_signal>(): {}` empty handler for every nondeterministic-branch signal of every required unit (Dezyne requires every provider output to be addressed).
    - `on s<i>.step(): <unit>.step();` step routing.

### Top (`Top.dzn`)

A `Top` component with a `system { ... }` block that instantiates the
`Network`, every `C<Unit>`, every `Step`, and wires them with `<=>` bindings.

### Step (`Step.dzn`)

A canonical clock component that emits `step` on `inevitable`. Imported by
every other file as `import Step.dzn;`.

## Translation semantics

The codegen makes the following deliberate choices, all concentrated in
[`src/codegen/codegen.py`](src/codegen/codegen.py):

- **One interface per unit**Control flows for main and Zenoh subscriber callbacks are grouped under a state machine in a single
  interface and are dispatched by `CurrentExecutionThread`. Each state machine is modelled to be driven by some external stepper component.
- **Single vs per-unit stepper** is a runtime flag (`--single-stepper`); default behavior is separate steppers per unit.
- **DeferTo(target)**:
  - `target == current_thread` → empty block (we're already there).
  - otherwise → assign `thread = target` and reset the current thread's
    state variable to 1 so the next re-entry restarts it.
- **Multi-successor transitions** are emitted as sibling `[s == k]` guards
  (Dezyne nondeterministic choice). Each branch fires a unique out-event
  (`<thread>_branch_<src>_to_<tgt>`) so the verifier can observe the choice. This is done to circumvent Dezyne's limitations on non-observable non-determinism.
- **Topic mangling** normalises Zenoh key expressions (e.g. `basic/B/A` → `basic_B_A`)
  and strips surrounding quotes that Joern emits on string literals.

## Project layout

```
src/
├── main.py                   CLI entry point
├── frontend/                 Joern HTTP API wrapper
│   ├── api.py                JoernQueryAPI (publishers, subscribers, CFGs)
│   ├── _connection.py        HTTP transport
│   └── _joern_parsers.py     Joern REPL response parsing
├── builders/                 TranslationUnit + InterconnectionGraph builders
│   ├── TUBuilder.py
│   ├── IGBuilder.py
│   └── builder.py
├── graphutils/               CFG (DOT) parsing utilities
├── datatypes/                TranslationUnit, StateMachine, etc.
└── codegen/                  Dezyne code generation
    ├── codegen.py            CodeGenerator + state_machines_to_code
    ├── _behavior.py          CFG → mid-IR StateMachine
    ├── _structural.py        Stepper / Network / Top generators
    ├── _naming.py            Topic mangling + filename → unit name
    └── ast/                  Dezyne AST node classes
        ├── ast.py            Base, TypeDecl, EventDecl, Block, File, ...
        ├── _interface.py     Guard, Trigger, Behavior, Interface
        └── _component.py     Provides, Requires, System, Binding, Component

tests/
├── codegen/                  state-machine, interface, structural, end-to-end
├── graphutils/               CFG / DOT / HTML parsing tests
└── test_interconnection.py   IGBuilder tests

examples/
├── basic-example/            Reference: A/B/C cross-publishing
├── dining-philosophers/
├── pgm-protocol/
├── pgm-class-lambda/
└── two-nodes/
```

## Development

Run the tests (uses `unittest`; no `pytest` required):

```bash
python -m unittest \
    tests.codegen.test_state_machine_generation \
    tests.codegen.test_interface_codegen \
    tests.codegen.test_structural \
    tests.codegen.test_end_to_end \
    tests.test_interconnection \
    tests.graphutils.test_cfg \
    tests.graphutils.test_dot_parser \
    tests.graphutils.test_parse_html
```

Or run a single module directly, e.g.

```bash
python -m unittest tests.codegen.test_end_to_end -v
```

The codegen tests use hand-built `InterconnectionGraph` fixtures and do not
require a running Joern server — only the full CLI end-to-end does.
