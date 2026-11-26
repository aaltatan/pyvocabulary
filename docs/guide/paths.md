# JSON-path errors

Compilers walk nested JSON definitions. An error deep inside should say where it happened,
without changing its type or message. `located(path, *errors)` adds an `at <path>` note
(`BaseException.add_note`) to errors of the given types raised in its block. `index_path`
and `key_path` build the paths.

```python
from pyvocabulary import Vocabulary, index_path, key_path, located

assert index_path("$.branches", 1) == "$.branches[1]"
assert key_path(index_path("$.branches", 1), "when") == "$.branches[1].when"

steps = Vocabulary[str]("step")

steps.add("click", "click()")

try:
    with located("$.expressions[0]", LookupError):
        steps["submit"]
except LookupError as error:
    assert type(error).__name__ == "NameDoesNotExistError"
    assert error.__notes__ == ["at $.expressions[0]"]
```

Errors of other types pass through untouched:

```python
from pyvocabulary import located

try:
    with located("$.expressions[0]", LookupError):
        raise ValueError("bad value")
except ValueError as error:
    assert not hasattr(error, "__notes__")
```

## Nested paths

When an inner block (or another package's compiler, which reports paths from its own root
`$`) already added a location, the outer path is **prefixed** onto it. The final note is the
absolute path in the outer document, and there is only ever one `at $...` note:

```python
from pyvocabulary import located

try:
    with located("$.branches[1].when", KeyError):
        with located("$.expressions[0]", KeyError):
            raise KeyError("itemz__ge")
except KeyError as error:
    assert error.__notes__ == ["at $.branches[1].when.expressions[0]"]
```

This is how a pyruleset decision that embeds pyspecification rules reports the full path of
a typo inside a rule.

!!! tip
    Add the note with `located`; never wrap the error in another exception type. Callers keep
    catching the exception class they expect, and the note shows up in tracebacks.
