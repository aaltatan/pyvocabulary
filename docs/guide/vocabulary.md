# Vocabularies

A `Vocabulary[F]` is a read-only `Mapping[str, F]` filled with `add`. The `kind` names what
the entries are and appears in error messages and the repr.

```python
from pyvocabulary import Vocabulary

steps = Vocabulary[str]("step")

assert steps.add("click", "click()") == "click()"

steps.add("fill", "fill()")

assert steps["click"] == "click()"
assert list(steps) == ["click", "fill"]
assert len(steps) == 2
assert "fill" in steps
assert repr(steps) == "Vocabulary[step](click, fill)"
```

Without a `kind`, entries are called "name": `Vocabulary[int]()`.

## Registering with a decorator

`add` returns the entry, so it fits inside a decorator:

```python
from collections.abc import Callable

from pyvocabulary import Vocabulary

rules = Vocabulary[Callable[[int], bool]]("rule")


def rule(function: Callable[[int], bool]) -> Callable[[int], bool]:
    return rules.add(function.__name__, function)


@rule
def is_positive(value: int) -> bool:
    return value > 0


assert rules["is_positive"](3)
```

## Errors

Unknown names list what is available. Names are checked when they are added, and cannot be
registered twice:

```python
from pyvocabulary import (
    InvalidNameError,
    NameAlreadyRegisteredError,
    NameDoesNotExistError,
    Vocabulary,
)

steps = Vocabulary[str]("step")

steps.add("click", "click()")
steps.add("fill", "fill()")

try:
    steps["submit"]
except NameDoesNotExistError as error:
    assert str(error) == "Step 'submit' does not exist. Available steps: click, fill"

try:
    steps.add("click", "again()")
except NameAlreadyRegisteredError as error:
    assert str(error) == "Step 'click' is already registered."

try:
    steps.add("double-click", "dblclick()")
except InvalidNameError as error:
    assert str(error).startswith("Invalid step name: 'double-click', ")
```

`NameDoesNotExistError` is a `LookupError` and `InvalidNameError` a `ValueError`, so generic
handlers still catch them. See [Exceptions](../reference/exceptions.md).

`get` returns a default instead of raising:

```python
from pyvocabulary import Vocabulary

steps = Vocabulary[str]("step")

steps.add("click", "click()")

assert steps.get("submit") is None
assert steps.get("submit", "noop()") == "noop()"
```

## Hidden entries

A hidden entry keeps its name taken, but is left out of lookups, iteration, length and
`labels`, so it never reaches a compiler or a JSON Schema. It stays usable from Python
through the object you got back from `add`.

```python
from pyvocabulary import NameAlreadyRegisteredError, Vocabulary

steps = Vocabulary[str]("step")

steps.add("click", "click()")
debug = steps.add("debug", "debug()", hidden=True)

assert debug == "debug()"
assert list(steps) == ["click"]
assert "debug" not in steps
assert steps.is_registered("debug")

try:
    steps.add("debug", "other()")
except NameAlreadyRegisteredError as error:
    assert str(error) == "Step 'debug' is already registered."
```

## Labels

`add(..., label=...)` stores a human-readable label next to the entry. `labels` returns a
new dict with the labels of the visible entries that have one:

```python
from pyvocabulary import Vocabulary

rules = Vocabulary[int]("rule")

rules.add("age__ge", 1, label={"en": "Age at least", "ar": "العمر لا يقل عن"})
rules.add("is_admin", 2)
rules.add("internal", 3, hidden=True, label="Internal")

assert rules.labels == {"age__ge": {"en": "Age at least", "ar": "العمر لا يقل عن"}}
```

A label is a non-empty string or a non-empty `{language: text}` map; anything else raises
`TypeError`. See [Labels and choices](labels.md).

## Injecting your own errors

Packages keep their own public exceptions and messages by injecting error factories:

| Argument | Called with | Default |
| --- | --- | --- |
| `does_not_exist` | the name and the visible names | `NameDoesNotExistError` |
| `already_registered` | the name | `NameAlreadyRegisteredError` |
| `invalid_name` | the name | `InvalidNameError` |

```python
from pyvocabulary import Vocabulary


class RuleDoesNotExistError(LookupError):
    def __init__(self, name, available):
        super().__init__(f"No rule {name!r}; try one of: {', '.join(available)}")


class InvalidRuleNameError(ValueError):
    pass


rules = Vocabulary[int](
    "rule",
    does_not_exist=RuleDoesNotExistError,
    invalid_name=lambda name: InvalidRuleNameError(f"Bad rule name: {name!r}"),
)

rules.add("age__ge", 1)

try:
    rules["age__gt"]
except RuleDoesNotExistError as error:
    assert str(error) == "No rule 'age__gt'; try one of: age__ge"

try:
    rules.add("1st", 2)
except InvalidRuleNameError as error:
    assert str(error) == "Bad rule name: '1st'"
```

`get` still works with injected errors that are `LookupError`s but not `KeyError`s:

```python
assert rules.get("age__gt", 0) == 0
```

!!! note
    `Mapping.get` only catches `KeyError`, so `Vocabulary` overrides it to check membership
    instead. Injected `does_not_exist` errors may be any exception type.
