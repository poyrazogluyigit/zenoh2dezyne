# Pub/Sub-to-Dezyne Model Translator

`zenoh2dezyne` is a static-analysis-driven translator that extracts the
publish/subscribe behaviour of a C++ application and emits an equivalent
[Dezyne](https://gitlab.com/dezyne/dezyne) formal model. The generated model is
suitable for verification with the Dezyne toolchain (mCRL2 underneath).

Despite the name, the translator is **middleware-neutral**: a `--middleware`
flag selects how publishers/subscribers are recognised, with extractors for
[Zenoh](https://zenoh.io/) (C++), ROS1/roscpp, and ROS2/rclcpp. All
framework-specific knowledge lives behind a single extractor seam; everything
downstream is framework-agnostic.

The repository ships with several example systems for testing and benchmarking:

- [`examples/basic-example`](examples/basic-example) — three units (A/B/C) cross-publishing on three topics (Zenoh).
- [`examples/dining-philosophers`](examples/dining-philosophers) — naive dining-philosophers solution (Zenoh).
- [`examples/pgm-protocol`](examples/pgm-protocol), [`pgm-class-lambda`](examples/pgm-class-lambda) — simplifications of the PGM (Pragmatic General Multicast) protocol (Zenoh).
- [`examples/two-nodes`](examples/two-nodes) — minimal two-node smoke test (Zenoh).
- [`examples/ros2-talker-listener`](examples/ros2-talker-listener) — minimal ROS2 publisher/subscriber.

In its current state, the code generator is validated against a hand-written
oracle only for `basic-example`.

## Roadmap

- [x] Append a source-file aggregation step before building translation units (using quom)
- [x] Generalise the frontend to multiple middlewares (Zenoh, ROS1, ROS2)
- [ ] Re-evaluate existing examples
- [ ] Add new examples

The examples are inspired by the [BEEM Benchmark Suite](https://github.com/plug-obp/beem-benchmark).

## Pipeline

The run is a fixed sequence of stages (`src/pipeline.py`, `STAGES`):

```
  Source tree (.cpp / .h, multi-file)
        │
        ▼  src/preprocess
  ┌──────────────────────┐   detect_nodes: files defining int main()
  │ detect → amalgamate  │   Amalgamator (quom): inline each node's deps into
  │ (quom)               │   one self-contained <node>.cpp  →  <out>/amalgamated/
  └──────────────────────┘
        │
        ▼
  ┌───────────────┐     ┌────────────────────────────┐
  │ Joern server  │ ──► │  src/frontend              │   JoernClient: generic
  │ (CPG analysis)│     │  JoernClient + extractors  │   queries (files, CFGs);
  └───────────────┘     └────────────────────────────┘   extractor: pubs/subs
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  src/builders      │   TUBuilder builds per-file
                        │  TUBuilder         │   TranslationUnits; _normalize
                        │  IGBuilder         │   tags publish nodes neutrally;
                        └────────────────────┘   IGBuilder links them by topic
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  src/codegen       │   CFG (neutral attrs) → mid-IR
                        │  CodeGenerator     │   StateMachine → AST → .dzn text
                        └────────────────────┘
                                  │
                                  ▼
                        Generated Dezyne files  →  <out>/models/
                        (one per unit + Network + Top + Step)
```

Each amalgamated translation unit becomes one `interface I<Unit>` (with all of
its threads dispatched by a `CurrentExecutionThread` enum) and a wrapping
`component C<Unit>`. Cross-unit communication is wired through a generated
`Network` component; the whole system is assembled in `Top`.

The extractor seam is the key design point: each extractor tags publish CFG
nodes with **neutral** `comm_op`/`topic` attributes (`src/builders/_normalize.py`),
so builders and codegen never touch framework-specific concepts.

## Requirements

- **Python 3.13+** (uses `X | Y` union annotations and the latest `dataclass` semantics).
- A running **[Joern](https://github.com/joernio/joern)** server (defaults to
  `http://localhost:8080`; a local server is spawned if none is reachable).
- **[quom](https://github.com/Viatorus/quom)** on `PATH` for code amalgamation.
- Python dependencies: `networkx`, `requests`, `pydot`, `quom` (in `requirements.txt`).

## Installation

```bash
git clone https://github.com/<you>/zenoh2dezyne.git
cd zenoh2dezyne
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optionally start a Joern server in a separate terminal (otherwise one is spawned):

```bash
joern --server
```

## Usage

```bash
python -m src.main --input <input-dir> [--output <output-dir>] [--middleware <mw>]
```

Where:
- `--input/-i` (**required**): Path to the source directory to analyze.
- `--output/-o` (optional): Output root for all generated files (default: `<cwd>/out`).
- `--middleware/-m` (optional): Pub/sub middleware — `zenoh` (default), `ros1`, or `ros2`.
- `--joern-server` (optional): URL of the Joern server (default: `http://localhost:8080`).
- `--logging/-l` (optional): Logging level (default: `WARNING`).

### Output directory layout

All intermediates and final models are written under the output root:

```
<output>/
├── amalgamated/     # one self-contained .cpp per node (quom output)
└── models/          # generated .dzn files (final models, flat)
```

(Joern keeps its own workspace in its default location — it is not placed under
the output directory.)

### Example

Analyze a multi-file Zenoh project:

```bash
python -m src.main --input examples/pgm-class-lambda --output /tmp/pgm-models
```

Results in:

```
/tmp/pgm-models/
├── amalgamated/
│   ├── sender.cpp      # sender.cpp + inlined includes
│   └── receiver.cpp    # receiver.cpp + inlined includes
└── models/
    ├── sender.dzn, receiver.dzn, Network.dzn, Top.dzn, Step.dzn
```

Analyze a ROS2 project:

```bash
python -m src.main --input examples/ros2-talker-listener -o /tmp/ros2-models -m ros2
```

## Supported input patterns

Generic structure (any middleware):
- Each `.cpp` defining `int main(...)` is detected as an entry point and becomes
  one translation unit. Headers are inlined by amalgamation, so multi-file /
  shared-header projects are supported.
- Topic key expressions should be **string literals**.
- Callbacks should be free functions or named lambdas.

Per middleware:
- **Zenoh** — `declare_publisher`, `session.put` (the session variable name is
  discovered dynamically — it need not be named `session`), and
  `declare_subscriber("topic", &cb, …)`.
- **ROS1 (roscpp)** — `advertise(...)` + `handle.publish(...)`, and
  `subscribe(..., cb)`.
- **ROS2 (rclcpp)** — `create_publisher(...)` + `handle->publish(...)`, and
  `create_subscription(..., &cb)`.

> ROS extraction anchors on the enclosing assignment rather than the call,
> because Joern's fuzzy C++ frontend misparses templated calls such as
> `create_publisher<T>(...)` (see `src/frontend/extractors/_ros_common.py`).

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
  - `requires IStep s<i>;` per unit.
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
every other file as `import Step.dzn;`. There is one `Step` instance per unit.

## Translation semantics

The codegen makes the following deliberate choices, concentrated in
[`src/codegen/codegen.py`](src/codegen/codegen.py) and
[`src/codegen/_behavior.py`](src/codegen/_behavior.py):

- **One interface per unit.** Control flows for `main` and subscriber callbacks
  are grouped under per-thread state machines in a single interface, dispatched
  by `CurrentExecutionThread`. Each is driven by an external stepper component.
- **DeferTo(target):**
  - `target == current_thread` → empty block (we're already there).
  - otherwise → assign `thread = target` and reset the current thread's state
    variable to 1 so the next re-entry restarts it.
- **Multi-successor transitions** are emitted as sibling `[s == k]` guards
  (Dezyne nondeterministic choice). Each branch fires a unique out-event
  (`<thread>_branch_<src>_to_<tgt>`) so the verifier can observe the choice. This
  circumvents Dezyne's limitations on non-observable non-determinism.
- **Topic mangling** strips the quotes Joern emits on string literals and maps
  `/` → `_` (e.g. `basic/B/A` → `basic_B_A`); see `src/codegen/_naming.py`.

## Project layout

```
src/
├── main.py                   CLI entry point (--input / --middleware)
├── context.py                RunContext: input/output paths (amalgamated, models)
├── pipeline.py               Pipeline + STAGES (detect→amalgamate→import→build→codegen→write)
├── preprocess/               Entry-point detection + quom amalgamation
│   ├── _detect.py            detect_nodes (files defining int main())
│   └── _amalgamate.py        Amalgamator (shells out to quom)
├── frontend/                 Joern access
│   ├── client.py             JoernClient — generic queries (files, CFGs, import/open/delete)
│   ├── _connection.py        HTTP transport (can spawn local Joern)
│   ├── _joern_parsers.py     Joern REPL response parsing
│   └── extractors/           Middleware seam
│       ├── base.py           MiddlewareExtractor Protocol + BaseExtractor
│       ├── __init__.py       EXTRACTORS registry + get_extractor()
│       ├── zenoh.py          ZenohExtractor
│       ├── ros1.py, ros2.py  ROS extractors
│       └── _ros_common.py    Shared ROS queries
├── builders/                 TranslationUnit + InterconnectionGraph builders
│   ├── builder.py
│   ├── TUBuilder.py
│   ├── _normalize.py         Tag publish CFG nodes with neutral comm_op/topic
│   └── IGBuilder.py
├── graphutils/               CFG (DOT) parsing utilities
├── datatypes/                TranslationUnit, Publisher, Subscriber, StateMachine, ...
└── codegen/                  Dezyne code generation
    ├── codegen.py            CodeGenerator + state_machines_to_code
    ├── _behavior.py          CFG → mid-IR StateMachine (reads neutral attrs only)
    ├── _structural.py        Stepper / Network / Top generators
    ├── _naming.py            Topic mangling + filename → unit name
    └── ast/                  Dezyne AST node classes
        ├── ast.py            Base, TypeDecl, EventDecl, Block, File, ...
        ├── _interface.py     Guard, Trigger, Behavior, Interface
        └── _component.py     Provides, Requires, System, Binding, Component

tests/
├── codegen/                  state-machine, interface, structural, end-to-end
├── builders/                 builder + normalize
├── frontend/                 zenoh/ros extractors, connection/workspace
├── preprocess/               detect, amalgamate
├── graphutils/               CFG / DOT / HTML parsing tests
├── datatypes/                neutral comm-model types
└── test_*.py                 context, pipeline, interconnection, CLI, gated real e2e

examples/
├── basic-example/            Reference: A/B/C cross-publishing (Zenoh)
├── dining-philosophers/
├── pgm-protocol/
├── pgm-class-lambda/
├── two-nodes/
└── ros2-talker-listener/     ROS2 publisher/subscriber
```

## Development

Run the tests (uses `unittest`; no `pytest` required). Mixed namespace packaging
means `unittest discover` mis-collects a module or two, so prefer the explicit
module list:

```bash
python -m unittest \
    tests.codegen.test_state_machine_generation \
    tests.codegen.test_interface_codegen \
    tests.codegen.test_structural \
    tests.codegen.test_end_to_end \
    tests.builders.test_builder_build \
    tests.builders.test_normalize \
    tests.datatypes.test_comm_model \
    tests.frontend.test_zenoh_extractor \
    tests.frontend.test_ros_extractors \
    tests.frontend.test_connection_workspace \
    tests.graphutils.test_cfg \
    tests.graphutils.test_dot_parser \
    tests.graphutils.test_parse_html \
    tests.graphutils.test_interconnection \
    tests.test_interconnection \
    tests.test_context \
    tests.test_pipeline \
    tests.test_main_cli \
    tests.preprocess.test_detect
```

Or run a single module directly, e.g.

```bash
python -m unittest tests.codegen.test_end_to_end -v
```

The codegen tests use hand-built `InterconnectionGraph` fixtures and do not
require a running Joern server. The real multi-file end-to-end test
(`tests/test_e2e_real.py`) needs real quom + Joern and is gated behind the
`JOERN_E2E` environment variable:

```bash
JOERN_E2E=1 python -m unittest tests.test_e2e_real -v
```
