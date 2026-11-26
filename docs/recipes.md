# Recipes

Complete, runnable programs. Each one is self-contained.

## A tiny compiler

A compiler for `{"all": [call, ...]}` documents, built from every piece: a vocabulary of
check factories, early argument binding with `bind_problem`, JSON-path notes with
`located`, and a JSON Schema from the signatures.

```python
from collections.abc import Callable
from inspect import signature
from typing import Any

from pyvocabulary import (
    JSON_SCHEMA_DIALECT,
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

assert in_range(5)
assert not in_range(11)

try:
    compile_all({"all": [{"name": "ge", "args": [1]}, {"name": "lt", "args": [10]}]})
except LookupError as error:
    assert str(error) == "Check 'lt' does not exist. Available checks: ge, le"
    assert error.__notes__ == ["at $.all[1]"]

try:
    compile_all({"all": [{"name": "ge", "args": [1, 2]}]})
except CheckError as error:
    assert str(error) == "ge: too_many"
    assert error.__notes__ == ["at $.all[0]"]

schema = {
    "$schema": JSON_SCHEMA_DIALECT,
    "type": "object",
    "properties": {
        "all": {
            "type": "array",
            "items": {"oneOf": [call_json_schema(name, factory) for name, factory in checks.items()]},
        },
    },
    "required": ["all"],
}

assert [call["description"] for call in schema["properties"]["all"]["items"]["oneOf"]] == [
    "Whether the value is at least `minimum`.",
    "Whether the value is at most `maximum`.",
]
```

## A package with its own errors

A package keeps its public exception hierarchy and messages, and still gets the registry for
free. This is the pattern pyspecification, pyformula and pyflowstep follow.

```python
from collections.abc import Callable

from pyvocabulary import Vocabulary


class PyrulesError(Exception): ...


class RuleDoesNotExistError(PyrulesError, LookupError):
    def __init__(self, name: str, available) -> None:
        super().__init__(f"Rule '{name}' does not exist. Available rules: {', '.join(available)}")


class RuleAlreadyRegisteredError(PyrulesError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Rule '{name}' is already registered.")


class InvalidRuleNameError(PyrulesError, ValueError):
    def __init__(self, name: object) -> None:
        super().__init__(f"Invalid rule name: {name!r}")


def rules_vocabulary() -> Vocabulary[Callable[..., bool]]:
    return Vocabulary[Callable[..., bool]](
        "rule",
        does_not_exist=RuleDoesNotExistError,
        already_registered=RuleAlreadyRegisteredError,
        invalid_name=InvalidRuleNameError,
    )


rules = rules_vocabulary()


def rule(*, hidden: bool = False, label: str | None = None):
    def decorator(function: Callable[..., bool]) -> Callable[..., bool]:
        return rules.add(function.__name__, function, hidden=hidden, label=label)

    return decorator


@rule(label="Is an adult")
def is_adult(age: int) -> bool:
    return age >= 18


@rule(hidden=True)
def is_test_user(name: str) -> bool:
    return name.startswith("test_")


assert list(rules) == ["is_adult"]
assert rules.labels == {"is_adult": "Is an adult"}
assert is_test_user("test_bob")

for attempt, expected in (
    (lambda: rules["is_test_user"], RuleDoesNotExistError),
    (lambda: rule()(is_adult), RuleAlreadyRegisteredError),
    (lambda: rules.add("is-adult", is_adult), InvalidRuleNameError),
):
    try:
        attempt()
    except PyrulesError as error:
        assert type(error) is expected
```

## Nested compilers with absolute paths

An outer compiler hands part of its document to an inner one. The inner compiler reports
paths from its own root `$`; `located` in the outer compiler turns them into absolute paths.

```python
from typing import Any

from pyvocabulary import Vocabulary, index_path, key_path, located

fields = Vocabulary[str]("field")

fields.add("age", "age")
fields.add("name", "name")


def compile_expression(expression: dict[str, Any]) -> list[str]:
    result = []

    for index, name in enumerate(expression["fields"]):
        with located(index_path("$.fields", index), LookupError):
            result.append(fields[name])

    return result


def compile_decision(decision: dict[str, Any]) -> list[list[str]]:
    result = []

    for index, branch in enumerate(decision["branches"]):
        with located(key_path(index_path("$.branches", index), "when"), LookupError):
            result.append(compile_expression(branch["when"]))

    return result


try:
    compile_decision(
        {
            "branches": [
                {"when": {"fields": ["age"]}},
                {"when": {"fields": ["name", "agee"]}},
            ],
        },
    )
except LookupError as error:
    assert error.__notes__ == ["at $.branches[1].when.fields[1]"]
```
