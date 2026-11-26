# Exceptions

```text
Exception
└── PyvocabularyError
    ├── NameDoesNotExistError          (also a LookupError)
    ├── NameAlreadyRegisteredError
    └── InvalidNameError               (also a ValueError)
```

These are the **defaults**. Packages built on pyvocabulary usually inject their own error
classes into a `Vocabulary`, so their users see the package's exceptions instead (see
[Injecting your own errors](../guide/vocabulary.md#injecting-your-own-errors)).

```python
from pyvocabulary import (
    InvalidNameError,
    NameAlreadyRegisteredError,
    NameDoesNotExistError,
    PyvocabularyError,
)

for error_type in (InvalidNameError, NameAlreadyRegisteredError, NameDoesNotExistError):
    assert issubclass(error_type, PyvocabularyError)

assert issubclass(NameDoesNotExistError, LookupError)
assert issubclass(InvalidNameError, ValueError)
```

## When each one is raised

| Exception | Raised by | Example message |
| --- | --- | --- |
| `NameDoesNotExistError(name, available, /, *, kind="name")` | `vocabulary[name]` for an unknown or hidden name | `Step 'submit' does not exist. Available steps: click, fill` |
| `NameAlreadyRegisteredError(name, /, *, kind="name")` | `Vocabulary.add` with a taken name | `Step 'click' is already registered.` |
| `InvalidNameError(name, /, *, kind="name")` | `validate_name`, `Vocabulary.add` | `Invalid step name: 'double-click', you should follow the python variable naming convention: ...` |

With no visible names, the list reads `(none)`:

```python
from pyvocabulary import NameDoesNotExistError

assert str(NameDoesNotExistError("click", [], kind="step")) == (
    "Step 'click' does not exist. Available steps: (none)"
)
```

## Other errors

| Error | Raised by |
| --- | --- |
| `TypeError` | an invalid `Text` in `Vocabulary.add(label=)`, `call_json_schema(label=)`, `labelled`, `Label` or `Choices` |
| `ValueError` | `Choices({})` |

`located` never raises its own errors: it re-raises the original exception with an
`at $...` note.
