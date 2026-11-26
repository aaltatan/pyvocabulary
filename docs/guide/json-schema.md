# JSON Schema

A building block is called from JSON as `{"name": ..., "args": [...], "kwargs": {...}}`. Its
signature already says what those may contain, so the schema is derived from it instead of
written by hand. All schemas are draft 2020-12 (`JSON_SCHEMA_DIALECT`).

## `json_schema_of`

`json_schema_of` turns a type annotation into a JSON Schema. Unknown or unannotated types
give `{}`, which accepts anything.

```python
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal, NotRequired, TypedDict

from pyvocabulary import json_schema_of

assert json_schema_of(int) == {"type": "integer"}
assert json_schema_of(Decimal) == {"type": "number"}
assert json_schema_of(date) == {"type": "string", "format": "date"}
assert json_schema_of(list[str]) == {"type": "array", "items": {"type": "string"}}

assert json_schema_of(dict[str, float]) == {
    "type": "object",
    "additionalProperties": {"type": "number"},
}

assert json_schema_of(int | None) == {"anyOf": [{"type": "integer"}, {"type": "null"}]}

assert json_schema_of(Literal["active", "pending"]) == {
    "enum": ["active", "pending"],
    "type": "string",
}


class Color(Enum):
    RED = 1
    GREEN = 2


assert json_schema_of(Color) == {"enum": [1, 2]}


class Item(TypedDict):
    sku: str
    quantity: NotRequired[int]


assert json_schema_of(Item) == {
    "type": "object",
    "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer"}},
    "required": ["sku"],
}

type Skus = list[str]

assert json_schema_of(Skus) == {"type": "array", "items": {"type": "string"}}
assert json_schema_of(object) == {}
```

The full table of supported types is in [Type mapping](../reference/type-mapping.md).

### `Process` markers

A parameter marked with a pyargprocessors `Process(fn)` is described by what `fn` accepts,
because that is what the JSON has to send:

```python
from datetime import date
from typing import Annotated

from pyargprocessors import Process

from pyvocabulary import json_schema_of


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


assert json_schema_of(Annotated[date, Process(parse_date)]) == {"type": "string"}
```

## `call_json_schema`

`call_json_schema(name, factory)` describes one JSON call of a building block from its
factory's signature:

- `name` is fixed with `const`;
- positional parameters go under `args`, as `prefixItems`;
- keyword-capable parameters go under `kwargs`;
- JSON-compatible defaults (`None`, `str`, `int`, `float`, `bool`, `list`, `dict`) become
  `default`;
- the docstring becomes `description`.

```python
from pyvocabulary import call_json_schema


def age__between(min_age: int, max_age: int = 120, *, inclusive: bool = True) -> bool:
    """Whether the age is within a range."""
    return True


schema = call_json_schema("age__between", age__between)

assert schema["type"] == "object"
assert schema["required"] == ["name"]
assert schema["additionalProperties"] is False
assert schema["properties"]["name"] == {"const": "age__between"}

assert schema["properties"]["args"] == {
    "type": "array",
    "prefixItems": [{"type": "integer"}, {"type": "integer", "default": 120}],
    "items": False,
}

assert schema["properties"]["kwargs"]["properties"] == {
    "min_age": {"type": "integer"},
    "max_age": {"type": "integer", "default": 120},
    "inclusive": {"type": "boolean", "default": True},
}

assert schema["description"] == "Whether the age is within a range."
```

### `*args`, `**kwargs` and required keywords

`*args` and `**kwargs` open up `items` and `additionalProperties`; required keyword-only
parameters land in `kwargs.required`. A factory with no positional parameters has no
`prefixItems` (draft 2020-12 requires it to be non-empty).

```python
from pyvocabulary import call_json_schema


def tag(*labels: str, by: str, **extra: int) -> None: ...


schema = call_json_schema("tag", tag)

assert schema["properties"]["args"] == {"type": "array", "items": {"type": "string"}}

kwargs = schema["properties"]["kwargs"]

assert kwargs["required"] == ["by"]
assert kwargs["additionalProperties"] == {"type": "integer"}
```

### Extending the call shape

Packages add their own keys with `extra_properties`, and change what is required with
`required`:

```python
from pyvocabulary import call_json_schema


def age__between(min_age: int, max_age: int = 120) -> bool:
    return True


schema = call_json_schema(
    "age__between",
    age__between,
    extra_properties={"inverse": {"type": "boolean"}},
    required=("name", "args"),
)

assert list(schema["properties"]) == ["name", "args", "kwargs", "inverse"]
assert schema["required"] == ["name", "args"]
```

`label=` adds an `x-label` to the call; see [Labels and choices](labels.md).

## A schema for a whole vocabulary

A schema for a vocabulary is one `oneOf` over its visible names. Hidden entries are left out
automatically:

```python
from collections.abc import Callable

from pyvocabulary import JSON_SCHEMA_DIALECT, Vocabulary, call_json_schema


def age__between(min_age: int, max_age: int = 120) -> bool:
    return True


rules = Vocabulary[Callable[..., bool]]("rule")

rules.add("age__between", age__between)
rules.add("internal", lambda: True, hidden=True)

document = {
    "$schema": JSON_SCHEMA_DIALECT,
    "oneOf": [call_json_schema(name, factory) for name, factory in rules.items()],
}

assert JSON_SCHEMA_DIALECT == "https://json-schema.org/draft/2020-12/schema"
assert [call["properties"]["name"]["const"] for call in document["oneOf"]] == ["age__between"]
```
