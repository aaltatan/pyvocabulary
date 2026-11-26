# Argument errors

Building blocks bind their arguments when they are built, so a wrong argument fails early
instead of when the block runs. `inspect.Signature.bind` raises a plain `TypeError`;
`bind_problem` says which kind it was, so each package can raise its own exception class.

```python
from inspect import signature

from pyvocabulary import bind_problem


def between(low: int, high: int = 10, /, *, inclusive: bool = True) -> None: ...


def problem(*args, **kwargs):
    try:
        signature(between).bind(*args, **kwargs)
    except TypeError as error:
        return bind_problem(error)

    return None


assert problem() == "missing"
assert problem(1, 2, 3) == "too_many"
assert problem(1, 2, strict=True) == "unexpected_keyword"
assert problem(1, high=2) == "positional_only"
assert problem(1, 2) is None
```

## The possible problems

`bind_problem` returns a `BindProblem`, or `None` for a message it does not recognise:

| `BindProblem` | `Signature.bind` message contains |
| --- | --- |
| `"positional_only"` | a positional-only argument passed as a keyword |
| `"missing"` | `missing a required` |
| `"too_many"` | `too many positional arguments` |
| `"unexpected_keyword"` | `got an unexpected keyword argument` |
| `"multiple_values"` | `multiple values for argument` |

```python
from pyvocabulary import bind_problem

assert bind_problem(TypeError("multiple values for argument 'low'")) == "multiple_values"
assert bind_problem(TypeError("something else")) is None
```

## Mapping problems to your exceptions

A typical package keeps one `ArgumentError` base and a subclass per problem it cares about:

```python
from inspect import signature

from pyvocabulary import bind_problem


class ArgumentError(TypeError): ...


class MissingArgumentError(ArgumentError): ...


class TooManyArgumentsError(ArgumentError): ...


ERRORS = {"missing": MissingArgumentError, "too_many": TooManyArgumentsError}


def bind(function, *args, **kwargs):
    try:
        return signature(function).bind(*args, **kwargs)
    except TypeError as error:
        raise ERRORS.get(bind_problem(error), ArgumentError)(str(error)) from error


def between(low: int, high: int = 10) -> None: ...


try:
    bind(between)
except MissingArgumentError as error:
    assert str(error) == "missing a required argument: 'low'"

try:
    bind(between, 1, unknown=2)
except ArgumentError as error:
    assert type(error) is ArgumentError
```
