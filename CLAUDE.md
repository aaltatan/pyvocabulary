# pyvocabulary

The shared core of the package family: a registry of named building blocks
(`Vocabulary`), name validation, classification of `Signature.bind` errors, JSON Schemas
generated from signatures (`json_schema_of`, `call_json_schema`), and JSON-path notes on
errors (`located`, `index_path`, `key_path`). pyspecification, pyflowstep and pyruleset
build on it; each keeps its own decorators, error classes and expression formats.

## The family

Each package wraps `Callable[[T], R]` in an immutable value with an algebra, plus the
same supporting pieces: a decorator that turns functions into factories, arguments
bound at build time, a registry (the vocabulary), a JSON compiler with JSON-path
errors, and a JSON Schema generated from signatures.

| Package | Wraps | Composes with | Status |
| --- | --- | --- | --- |
| pyspecification | `T -> bool` | `&` `\|` `~` | released |
| pyformula | `T -> number` | arithmetic operators | released |
| pyflowstep | `T -> T` | `>>` | released |
| pyvocabulary | shared core: `Vocabulary`, JSON Schema, path notes | — | 0.1 built, not published |
| pyruleset | `T -> V`, first match wins | `\|` | 0.1 built, not published |
| pyordering | `T -> sort key` | `>>`, `~` | planned |
| pyaggregation | `Iterable[T] -> dict` | `&` | planned |
| pyprojection | `T -> dict` | `&` | planned |

All repositories live side by side in `~/dev/<name>` on the author's machine.

## Commands

```bash
uv sync                                   # create .venv with dev dependencies
uv run pytest                             # tests and doctests
uv run pytest --cov --cov-branch          # with branch coverage
uv run --python 3.12 pytest               # on the minimum supported version
uvx ruff check . && uvx ruff format --check .
uvx pyright src                           # strict type checking, no blanket ignores
```

The package is `pyvocabulary` under `src/`, built with `uv_build`.

## Design rules for this package

- Keep it small. Only code that at least two sibling packages already duplicate belongs here.
- Never own an expression format or a compiler. Those stay in each package.
- Packages inject their own error classes (`does_not_exist=`, `already_registered=`,
  `invalid_name=`), so their public exceptions and messages never change.
- `Vocabulary` is a read-only `Mapping` of *visible* names; hidden names are still taken.
  `get` is overridden because injected errors are `LookupError`s, not `KeyError`s.
- `located` prefixes outer paths onto inner `at $...` notes, so nested compilers report
  absolute paths (`at $.branches[1].when.expressions[0]`).
- Names use `fullmatch` (a trailing newline is not a valid name).
- Runtime dependency: `pyargprocessors` only (for `Process` markers in schemas).

## Code style (non-negotiable)

- Python 3.12+, PEP 695 generics (`class Ruleset[T, V]:`, `type Value[T, V] = Callable[[T], V]`).
- Simplest thing that works. No abstraction until a second real use exists.
- Functions first; a class only when it holds state or gives a nicer API (composable operators).
- Pure core, side effects at the edges. Composition over inheritance. No ABCs; use `Protocol`.
- Immutable values: `@dataclass(frozen=True, slots=True)`; operators return new objects.
- Fail early: validate when something is built, not when it runs.
- Full type hints, `collections.abc` imports, `Literal`/`TypedDict`/`Protocol` where they fit.
- `/` for positional-only, `*` for keyword-only (always for boolean flags).
- Guard clauses, `match`, comprehensions, walrus where it reads better. `pathlib`, never `os.path`.
- Errors: a package base exception, specific subclasses, message built before `raise`
  (ruff EM), `raise X from error` when translating. Messages say what is wrong and what
  is valid: "Rule 'foo' does not exist. Available rules: a, b, c".
- JSON-path context is added as an exception note via `pyvocabulary.located`, never
  by wrapping the error in another type.
- Google-style docstrings with runnable doctests in ```python blocks. Comment only the *why*.
- Public functions first, `_private` helpers below; `# ---` section comments in long modules.
- Tests: `class TestThing:` with behaviour-named methods, fixtures in `conftest.py`,
  `pytest.raises(..., match=...)`. Branch coverage on.
- Ask before adding a runtime dependency. Do not add features, options or layers nobody asked for.

## How to work here

1. Read `PHASES.md`. Work on the first unchecked item only.
2. Write the test first, then the code. Keep doctests runnable.
3. Before ticking a box, run the full check (commands above) on Python 3.12 and 3.13.
4. Tick the box in `PHASES.md` in the same commit as the work.
5. Small commits on a branch; never push or publish unless asked.

## Kickoff prompt for a new conversation

Paste this into a new Claude conversation linked to this computer:

> You are working on `pyvocabulary` in `~/dev/pyvocabulary`. Read `CLAUDE.md` and `PHASES.md` there
> first and follow them exactly. Continue with the next unchecked phase. Work on a new git branch, run the full check on
> Python 3.12 and 3.13, tick what you finish in `PHASES.md`, and commit. Do not push or
> publish. When done, summarise what changed and what the next unchecked item is.
