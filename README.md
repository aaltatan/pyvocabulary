# pyvocabulary

The shared core of composable, JSON-definable building blocks, used by
[pyspecification](https://github.com/aaltatan/pyspecification),
[pyformula](https://github.com/aaltatan/pyformula),
[pyflowstep](https://github.com/aaltatan/pyflowstep) and
[pyruleset](https://github.com/aaltatan/pyruleset).

Each of those packages lets you register named building blocks (rules, steps, formula
variables), call them from JSON as `{"name": ..., "args": [...], "kwargs": {...}}`, and
generate a JSON Schema for that JSON. pyvocabulary is the part they all share:

| Piece | What it does |
| --- | --- |
| [`Vocabulary[F]`](#vocabulary) | Named entries, hidden entries, lookups with "Available ..." errors; packages inject their own error classes |
| [`validate_name`](#validate_name) | ASCII identifier check for names used in JSON |
| [`bind_problem`](#bind_problem) | Classifies `Signature.bind` errors so each package raises its own `ArgumentError` subclass |
| [`json_schema_of`, `call_json_schema`](#json-schemas) | JSON Schema of a type annotation, and of a `{"name", "args", "kwargs"}` call from a signature |
| [`located`, `index_path`, `key_path`](#json-path-errors) | Adds `at $.path` notes to errors, prefixing paths across nested compilers |

It does not own an expression format or a compiler: those stay in each package.

## Installation

```bash
pip install pyvocabulary
```

or with uv:

```bash
uv add pyvocabulary
```

Python 3.12+. The only runtime dependency is
[pyargprocessors](https://github.com/aaltatan/pyargprocessors) (for `Process` markers in
schemas).

## Vocabulary

A `Vocabulary[F]` is a read-only `Mapping[str, F]` filled with `add`. The `kind` names
what the entries are, and is used in error messages.

```python
from pyvocabulary import Vocabulary

steps = Vocabulary[str]("step")

steps.add("click", "click()")  # returns 'click()'
steps.add("fill", "fill()")

print(steps["click"])  # click()
print(list(steps), len(steps), "fill" in steps)  # ['click', 'fill'] 2 True
print(repr(steps))  # Vocabulary[step](click, fill)
```

`add` returns the entry, so it fits inside a decorator:

```python
from collections.abc import Callable

rules = Vocabulary[Callable[[int], bool]]("rule")


def rule(function: Callable[[int], bool]) -> Callable[[int], bool]:
    return rules.add(function.__name__, function)


@rule
def is_positive(value: int) -> bool:
    return value > 0


print(rules["is_positive"](3))  # True
```

### Errors

Unknown names list what is available. Names are checked when they are added, and
cannot be registered twice:

```python
from pyvocabulary import InvalidNameError, NameAlreadyRegisteredError, NameDoesNotExistError

try:
    steps["submit"]
except NameDoesNotExistError as error:
    print(error)  # Step 'submit' does not exist. Available steps: click, fill

try:
    steps.add("click", "again()")
except NameAlreadyRegisteredError as error:
    print(error)  # Step 'click' is already registered.

try:
    steps.add("double-click", "dblclick()")
except InvalidNameError as error:
    print(error)  # Invalid step name: 'double-click', ...
```

`get` returns a default instead of raising:

```python
print(steps.get("submit"))  # None
print(steps.get("submit", "noop()"))  # noop()
```

### Hidden entries

A hidden entry keeps its name taken, but is left out of lookups, iteration and length,
so it never reaches a compiler or a JSON Schema. It stays usable from Python through
the object you got back from `add`.

```python
debug = steps.add("debug", "debug()", hidden=True)

print(list(steps), "debug" in steps, steps.is_registered("debug"))  # ['click', 'fill'] False True

try:
    steps.add("debug", "other()")
except NameAlreadyRegisteredError as error:
    print(error)  # Step 'debug' is already registered.
```

### Injecting your own errors

Packages keep their own public exceptions and messages by injecting error factories.
`does_not_exist` gets the name and the visible names, `already_registered` and
`invalid_name` get the name:

```python
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
    print(error)  # No rule 'age__gt'; try one of: age__ge

try:
    rules.add("1st", 2)
except InvalidRuleNameError as error:
    print(error)  # Bad rule name: '1st'
```

`get` still works with injected errors that are `LookupError`s but not `KeyError`s:

```python
print(rules.get("age__gt", 0))  # 0
```

## validate_name

Names end up in JSON, error messages and reprs, so they are ASCII Python identifiers.
`validate_name` returns the name unchanged or raises (`InvalidNameError` is also a
`ValueError`). A trailing newline is not accepted.

```python
from pyvocabulary import InvalidNameError, validate_name

print(validate_name("add_milk"))  # add_milk

try:
    validate_name("add_milk\n")
except InvalidNameError as error:
    print(error)  # Invalid name: 'add_milk\n', ...

try:
    validate_name(42, kind="formula")
except InvalidNameError as error:
    print(error)  # Invalid formula name: 42, ...

try:
    validate_name("é", error=lambda name: KeyError(name))
except KeyError as error:
    print(repr(error))  # KeyError('é')
```

## bind_problem

Building blocks bind their arguments when they are built, so a wrong argument fails
early. `Signature.bind` raises a plain `TypeError`; `bind_problem` says which kind it
was, so each package can raise its own exception class:

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


print(problem())  # missing
print(problem(1, 2, 3))  # too_many
print(problem(1, 2, strict=True))  # unexpected_keyword
print(problem(1, high=2))  # positional_only
print(problem(1, 2))  # None
```

The possible values are the `BindProblem` literal: `"positional_only"`, `"missing"`,
`"too_many"`, `"unexpected_keyword"`, `"multiple_values"`. Unknown messages give `None`.

A typical mapping in a package:

```python
class ArgumentError(TypeError): ...


class MissingArgumentError(ArgumentError): ...


class TooManyArgumentsError(ArgumentError): ...


ERRORS = {"missing": MissingArgumentError, "too_many": TooManyArgumentsError}


def bind(function, *args, **kwargs):
    try:
        return signature(function).bind(*args, **kwargs)
    except TypeError as error:
        raise ERRORS.get(bind_problem(error), ArgumentError)(str(error)) from error


try:
    bind(between)
except MissingArgumentError as error:
    print(error)  # missing a required argument: 'low'
```

## JSON Schemas

### json_schema_of

`json_schema_of` turns a type annotation into a JSON Schema (draft 2020-12, see
`JSON_SCHEMA_DIALECT`). Unknown or unannotated types give `{}`, which accepts anything.

```python
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal, NotRequired, TypedDict

from pyvocabulary import json_schema_of

print(json_schema_of(int))  # {'type': 'integer'}
print(json_schema_of(Decimal))  # {'type': 'number'}
print(json_schema_of(date))  # {'type': 'string', 'format': 'date'}
print(json_schema_of(list[str]))  # {'type': 'array', 'items': {'type': 'string'}}

print(json_schema_of(dict[str, float]))
# {'type': 'object', 'additionalProperties': {'type': 'number'}}

print(json_schema_of(int | None))  # {'anyOf': [{'type': 'integer'}, {'type': 'null'}]}

print(json_schema_of(Literal["active", "pending"]))
# {'enum': ['active', 'pending'], 'type': 'string'}


class Color(Enum):
    RED = 1
    GREEN = 2


print(json_schema_of(Color))  # {'enum': [1, 2]}


class Item(TypedDict):
    sku: str
    quantity: NotRequired[int]


print(json_schema_of(Item))
# {'type': 'object',
#  'properties': {'sku': {'type': 'string'}, 'quantity': {'type': 'integer'}},
#  'required': ['sku']}

type Skus = list[str]

print(json_schema_of(Skus))  # {'type': 'array', 'items': {'type': 'string'}}
print(json_schema_of(object))  # {}
```

Supported: `str`, `int`, `float`, `Decimal`, `bool`, `None`, `datetime`, `date`, `time`,
`UUID`, `list`/`tuple`/`set`/`frozenset`, `dict`, unions, `Literal`, `Enum`, `TypedDict`,
`type` aliases, `Annotated`, `Required` and `NotRequired`.

A parameter marked with a pyargprocessors `Process(fn)` is described by what `fn`
accepts, because that is what the JSON has to send:

```python
from typing import Annotated

from pyargprocessors import Process


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


print(json_schema_of(Annotated[date, Process(parse_date)]))  # {'type': 'string'}
```

### call_json_schema

`call_json_schema(name, factory)` describes one JSON call of a building block from its
factory's signature: positional parameters under `args` (as `prefixItems`),
keyword-capable ones under `kwargs`, JSON-compatible defaults as `default`, and the
docstring as `description`.

```python
from pyvocabulary import call_json_schema


def age__between(min_age: int, max_age: int = 120, *, inclusive: bool = True) -> bool:
    """Whether the age is within a range."""
    return True


schema = call_json_schema("age__between", age__between)

print(schema["type"], schema["required"], schema["additionalProperties"])  # object ['name'] False
print(schema["properties"]["name"])  # {'const': 'age__between'}

print(schema["properties"]["args"])
# {'type': 'array',
#  'prefixItems': [{'type': 'integer'}, {'type': 'integer', 'default': 120}],
#  'items': False}

print(schema["properties"]["kwargs"]["properties"])
# {'min_age': {'type': 'integer'},
#  'max_age': {'type': 'integer', 'default': 120},
#  'inclusive': {'type': 'boolean', 'default': True}}

print(schema["description"])  # Whether the age is within a range.
```

`*args` and `**kwargs` open up `items` and `additionalProperties`; required keyword-only
parameters land in `kwargs.required`:

```python
def tag(*labels: str, by: str, **extra: int) -> None: ...


schema = call_json_schema("tag", tag)

print(schema["properties"]["args"]["items"])  # {'type': 'string'}

kwargs = schema["properties"]["kwargs"]

print(kwargs["required"], kwargs["additionalProperties"])  # ['by'] {'type': 'integer'}
```

Packages add their own keys to the call shape with `extra_properties`, and change what
is required with `required`:

```python
schema = call_json_schema(
    "age__between",
    age__between,
    extra_properties={"inverse": {"type": "boolean"}},
    required=("name", "args"),
)

print(list(schema["properties"]), schema["required"])
# ['name', 'args', 'kwargs', 'inverse'] ['name', 'args']
```

A schema for a whole vocabulary is then one `oneOf` over its visible names:

```python
from pyvocabulary import JSON_SCHEMA_DIALECT

rules = Vocabulary[Callable[..., bool]]("rule")

rules.add("age__between", age__between)
rules.add("internal", lambda: True, hidden=True)

document = {
    "$schema": JSON_SCHEMA_DIALECT,
    "oneOf": [call_json_schema(name, factory) for name, factory in rules.items()],
}

print([call["properties"]["name"]["const"] for call in document["oneOf"]])  # ['age__between']
```

## JSON-path errors

Compilers walk nested JSON definitions. An error deep inside should say where it
happened, without changing its type or message. `located(path, *errors)` adds an
`at <path>` note to errors of the given types raised in its block; `index_path` and
`key_path` build the paths.

```python
from pyvocabulary import index_path, key_path, located

print(index_path("$.branches", 1))  # $.branches[1]
print(key_path(index_path("$.branches", 1), "when"))  # $.branches[1].when

try:
    with located("$.expressions[0]", LookupError):
        steps["submit"]
except LookupError as error:
    print(type(error).__name__, error.__notes__)  # NameDoesNotExistError ['at $.expressions[0]']
```

Errors of other types pass through untouched. Paths nest: when an inner block (or
another package's compiler, which reports paths from its own root `$`) already added a
location, the outer path is prefixed onto it, so the final note is the absolute path in
the outer document:

```python
try:
    with located("$.branches[1].when", LookupError):
        with located("$.expressions[0]", LookupError):
            steps["submit"]
except LookupError as error:
    print(error.__notes__)  # ['at $.branches[1].when.expressions[0]']
```

## Putting it together

A tiny compiler for `{"all": [call, ...]}` documents, built from every piece above:

```python
from collections.abc import Callable
from inspect import signature
from typing import Any

from pyvocabulary import (
    Vocabulary,
    bind_problem,
    call_json_schema,
    index_path,
    key_path,
    located,
)

type Check = Callable[[int], bool]


class CheckError(Exception): ...


class CheckArgumentError(CheckError, TypeError): ...


checks = Vocabulary[Callable[..., Check]]("check")


def check(factory):
    return checks.add(factory.__name__, factory)


@check
def ge(minimum: int) -> Check:
    """Whether the value is at least `minimum`."""
    return lambda value: value >= minimum


@check
def le(maximum: int) -> Check:
    """Whether the value is at most `maximum`."""
    return lambda value: value <= maximum


def build(call: dict[str, Any]) -> Check:
    factory = checks[call["name"]]
    args, kwargs = call.get("args", []), call.get("kwargs", {})

    try:
        signature(factory).bind(*args, **kwargs)
    except TypeError as error:
        message = f"{call['name']}: {bind_problem(error) or error}"
        raise CheckArgumentError(message) from error

    return factory(*args, **kwargs)


def compile_all(document: dict[str, Any]) -> Check:
    path = key_path("$", "all")
    built = []

    for index, call in enumerate(document["all"]):
        with located(index_path(path, index), LookupError, CheckError):
            built.append(build(call))

    return lambda value: all(item(value) for item in built)


in_range = compile_all({"all": [{"name": "ge", "args": [1]}, {"name": "le", "args": [10]}]})

print(in_range(5), in_range(11))  # True False

try:
    compile_all({"all": [{"name": "ge", "args": [1]}, {"name": "lt", "args": [10]}]})
except LookupError as error:
    print(error, *error.__notes__, sep="\n")
    # Check 'lt' does not exist. Available checks: ge, le
    # at $.all[1]

try:
    compile_all({"all": [{"name": "ge", "args": [1, 2]}]})
except CheckError as error:
    print(error, *error.__notes__, sep="\n")
    # ge: too_many
    # at $.all[0]

print([call_json_schema(name, factory)["description"] for name, factory in checks.items()])
# ['Whether the value is at least `minimum`.', 'Whether the value is at most `maximum`.']
```

## API reference

| Name | Kind | Summary |
| --- | --- | --- |
| `Vocabulary[F](kind="name", /, *, does_not_exist=None, already_registered=None, invalid_name=None)` | class | Read-only `Mapping[str, F]` of visible names |
| `Vocabulary.add(name, entry, /, *, hidden=False) -> F` | method | Register and return `entry` |
| `Vocabulary.is_registered(name, /) -> bool` | method | Whether the name is taken, hidden or not |
| `validate_name(name, /, *, kind="name", error=None) -> str` | function | Return the name if it is an ASCII identifier, else raise |
| `bind_problem(error, /) -> BindProblem \| None` | function | Classify a `Signature.bind` `TypeError` |
| `BindProblem` | type | `Literal["positional_only", "missing", "too_many", "unexpected_keyword", "multiple_values"]` |
| `json_schema_of(annotation) -> dict` | function | JSON Schema of a type annotation |
| `call_json_schema(name, factory, /, *, extra_properties=None, required=("name",)) -> dict` | function | JSON Schema of one `{"name", "args", "kwargs"}` call |
| `JSON_SCHEMA_DIALECT` | constant | `"https://json-schema.org/draft/2020-12/schema"` |
| `located(path, /, *errors)` | context manager | Add or prefix an `at $...` note on matching errors |
| `index_path(path, index, /) -> str` | function | `"$.a"`, `2` → `"$.a[2]"` |
| `key_path(path, key, /) -> str` | function | `"$.a"`, `"b"` → `"$.a.b"` |
| `PyvocabularyError` | exception | Base class of the errors below |
| `NameDoesNotExistError` | exception | Unknown name; also a `LookupError` |
| `NameAlreadyRegisteredError` | exception | Name registered twice |
| `InvalidNameError` | exception | Name is not an ASCII identifier; also a `ValueError` |

## Development

```bash
uv sync
uv run pytest --cov --cov-branch
uvx ruff check . && uvx ruff format --check .
uvx pyright src
```

## License

GPL-3.0-only.
