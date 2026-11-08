# pyvocabulary

The shared core of composable, JSON-definable building blocks, used by
[pyspecification](https://github.com/aaltatan/pyspecification),
[pyflowstep](https://github.com/aaltatan/pyflowstep) and
[pyruleset](https://github.com/aaltatan/pyruleset).

```python
>>> from pyvocabulary import Vocabulary, call_json_schema, located
>>> steps = Vocabulary[str]("step")
>>> steps.add("click", "click()")
'click()'
>>> steps["fill"]
Traceback (most recent call last):
...
pyvocabulary.exceptions.NameDoesNotExistError: Step 'fill' does not exist. Available steps: click
```

| Piece | What it does |
| --- | --- |
| `Vocabulary[F]` | Named entries, hidden entries, lookups with "Available ..." errors; packages inject their own error classes |
| `validate_name` | ASCII identifier check for names used in JSON |
| `bind_problem` | Classifies `Signature.bind` errors so each package raises its own `ArgumentError` subclass |
| `json_schema_of`, `call_json_schema` | JSON Schema of a type annotation, and of a `{"name", "args", "kwargs"}` call from a signature |
| `located`, `index_path`, `key_path` | Adds `at $.path` notes to errors, prefixing paths across nested compilers |

Python 3.12+. Licensed GPL-3.0-only.
