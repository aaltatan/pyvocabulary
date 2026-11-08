# PHASES

## Phase 0 — Scaffold
- [x] `uv init --lib`, Python 3.12, `uv_build`, ruff `ALL`, pytest with doctests, branch coverage config
- [x] CLAUDE.md, PHASES.md, README.md, LICENSE

## Phase 1 — Core 0.1
- [x] `Vocabulary[F]` with injected error factories, hidden entries, `is_registered`, `get`
- [x] `validate_name` (uses `fullmatch`; rejects a trailing newline)
- [x] `bind_problem` for `Signature.bind` errors
- [x] `json_schema_of`, `call_json_schema` (extracted from pyspecification and pyflowstep)
- [x] `located`, `index_path`, `key_path` with nested path prefixing
- [x] 75 tests passing on Python 3.12 and 3.13; ruff, pyright and `mypy --strict` clean
- [x] Branch coverage measured: 100% (164 statements, 32 branches)

## Phase 2 — Adoption
- [x] pyspecification on pyvocabulary (branch `refactor/pyvocabulary`)
- [x] pyflowstep on pyvocabulary (branch `refactor/pyvocabulary`)
- [x] pyruleset uses `located`, `index_path`, `key_path`
- [ ] pyformula: decide whether it may depend on pyvocabulary (it has no pyargprocessors dependency today)

## Phase 3 — Release
- [ ] Create the GitHub repository `aaltatan/pyvocabulary` and push
- [ ] CI: ruff, pyright, pytest on 3.12 and 3.13 with coverage
- [ ] Confirm the PyPI name is free, publish 0.1.0
- [ ] Switch siblings from the git source to `pyvocabulary>=0.1.0` from PyPI and merge their PRs

## Later (only on a real need)
- [ ] Helpers for embedding one package's JSON Schema inside another's (`$id` per embedded schema)
