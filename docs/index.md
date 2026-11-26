# pyvocabulary

**The shared core of composable, JSON-definable building blocks.**

[pyspecification](https://github.com/aaltatan/pyspecification),
[pyformula](https://github.com/aaltatan/pyformula),
[pyflowstep](https://github.com/aaltatan/pyflowstep) and
[pyruleset](https://github.com/aaltatan/pyruleset) all let you register named building
blocks (rules, steps, formula variables), call them from JSON as
`{"name": ..., "args": [...], "kwargs": {...}}`, and generate a JSON Schema for that JSON.
pyvocabulary is the part they share.

| Piece | What it does |
| --- | --- |
| [`Vocabulary[F]`](guide/vocabulary.md) | Named entries, hidden entries, lookups with "Available ..." errors; packages inject their own error classes |
| [`validate_name`](guide/names.md) | ASCII identifier check for names used in JSON |
| [`bind_problem`](guide/arguments.md) | Classifies `Signature.bind` errors so each package raises its own `ArgumentError` subclass |
| [`json_schema_of`, `call_json_schema`](guide/json-schema.md) | JSON Schema of a type annotation, and of a `{"name", "args", "kwargs"}` call from a signature |
| [`Label`, `Choices`, `labelled`](guide/labels.md) | Human-readable labels in one language or several, for schema-driven editors |
| [`located`, `index_path`, `key_path`](guide/paths.md) | Adds `at $.path` notes to errors, prefixing paths across nested compilers |

It does **not** own an expression format or a compiler: those stay in each package.

## A first taste

```python
from pyvocabulary import NameDoesNotExistError, Vocabulary, call_json_schema

rules = Vocabulary[object]("rule")


def age__between(min_age: int, max_age: int = 120) -> bool:
    """Whether the age is within a range."""
    return True


rules.add("age__between", age__between)

assert list(rules) == ["age__between"]

try:
    rules["age__gt"]
except NameDoesNotExistError as error:
    assert str(error) == "Rule 'age__gt' does not exist. Available rules: age__between"

schema = call_json_schema("age__between", rules["age__between"])

assert schema["properties"]["args"]["prefixItems"] == [
    {"type": "integer"},
    {"type": "integer", "default": 120},
]
assert schema["description"] == "Whether the age is within a range."
```

The registry gave a helpful error for a typo, and the factory's signature became the JSON
Schema of the call, with no schema written by hand.

## Where to next

<div class="grid cards" markdown>

- [**Installation**](install.md): one command.
- [**User guide**](guide/index.md): every piece, one page each.
- [**Recipes**](recipes.md): a tiny compiler built from all the pieces.
- [**API reference**](reference/api.md): every public name.

</div>
