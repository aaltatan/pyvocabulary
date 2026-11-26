# API

## Vocabularies

### `Vocabulary[F]`

```py
Vocabulary[F](
    kind: str = "name",
    /,
    *,
    does_not_exist: Callable[[str, Iterable[str]], Exception] | None = None,
    already_registered: Callable[[str], Exception] | None = None,
    invalid_name: Callable[[object], Exception] | None = None,
)
```

A read-only `Mapping[str, F]` of the **visible** names, filled with `add`. `kind` names the
entries in default error messages and the repr.

| Member | Description |
| --- | --- |
| `add(name, entry, /, *, hidden=False, label=None) -> F` | validate `name`, register `entry` and return it |
| `labels -> dict[str, Text]` | property: a new dict of the labels of visible entries that have one |
| `is_registered(name, /) -> bool` | whether `name` is taken, hidden or not |
| `vocabulary[name]` | the entry; raises the `does_not_exist` error for unknown or hidden names |
| `get(name, default=None, /)` | the entry, or `default`; never raises |
| `name in vocabulary`, `iter`, `len`, `keys`, `values`, `items` | visible entries only |
| `repr(vocabulary)` | `Vocabulary[step](click, fill)` |

`add` raises the `invalid_name` error (default `InvalidNameError`) for a name that is not an
identifier, the `already_registered` error (default `NameAlreadyRegisteredError`) for a taken
name, and `TypeError` for an invalid `label`.

Guide: [Vocabularies](../guide/vocabulary.md).

## Names

### `validate_name`

```py
validate_name(
    name: object,
    /,
    *,
    kind: str = "name",
    error: Callable[[object], Exception] | None = None,
) -> str
```

Return `name` unchanged if it fully matches `[a-zA-Z_][a-zA-Z0-9_]*`; otherwise raise
`error(name)`, or `InvalidNameError(name, kind=kind)` when no `error` is given.

Guide: [Names](../guide/names.md).

## Argument errors

### `bind_problem`

```py
bind_problem(error: TypeError, /) -> BindProblem | None
```

Classify the `TypeError` raised by `inspect.Signature.bind`; `None` for an unknown message.

### `BindProblem`

```py
type BindProblem = Literal[
    "positional_only", "missing", "too_many", "unexpected_keyword", "multiple_values"
]
```

Guide: [Argument errors](../guide/arguments.md).

## JSON Schema

### `json_schema_of`

```py
json_schema_of(annotation: Any) -> dict[str, Any]
```

The JSON Schema of a type annotation; `{}` for unknown types. See
[Type mapping](type-mapping.md).

### `call_json_schema`

```py
call_json_schema(
    name: str,
    factory: Callable[..., Any],
    /,
    *,
    extra_properties: Mapping[str, dict[str, Any]] | None = None,
    required: tuple[str, ...] = ("name",),
    label: Text | None = None,
) -> dict[str, Any]
```

The JSON Schema of one `{"name": ..., "args": [...], "kwargs": {...}}` call:

| Key | Value |
| --- | --- |
| `type` | `"object"` |
| `properties.name` | `{"const": name}` |
| `properties.args` | array; positional parameters as `prefixItems` (left out when empty); `items` is the `*args` schema or `false` |
| `properties.kwargs` | object of keyword-capable parameters; `required` lists keyword-only ones without default; `additionalProperties` is the `**kwargs` schema or `false` |
| `properties.*` | plus `extra_properties` |
| `required` | `list(required)` |
| `additionalProperties` | `false` |
| `description` | the stripped docstring, when there is one |
| `x-label` | `label`, when given |

Parameter defaults that are `None`, `str`, `int`, `float`, `bool`, `list` or `dict` are
copied as `default`. Annotations are resolved through pyargprocessors, so string
annotations and `Process` markers work.

### `JSON_SCHEMA_DIALECT`

```py
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
```

Guide: [JSON Schema](../guide/json-schema.md).

## Labels

### `Text`

```py
type Text = str | Mapping[str, str]
```

One text for every language, or a `{language: text}` map. Must be non-empty, with non-empty
string values; otherwise `TypeError`.

### `labelled`

```py
labelled(
    schema: Mapping[str, Any],
    /,
    *,
    label: Text | None = None,
    description: Text | None = None,
) -> dict[str, Any]
```

A copy of `schema` with `x-label` and `x-description` added when given.

### `Label`

```py
@dataclass(frozen=True, slots=True)
class Label:
    label: Text
    description: Text | None = None
```

`Annotated` marker: adds `x-label` (and `x-description`) to an argument's schema. Texts are
checked when the marker is created.

### `Choices`

```py
@dataclass(frozen=True, slots=True)
class Choices:
    choices: Mapping[Any, Text]
```

`Annotated` marker: adds `enum` (the keys) and `x-choices` (`[{"value", "label"}, ...]`).
Raises `ValueError` when empty and `TypeError` for an invalid label.

Guide: [Labels and choices](../guide/labels.md).

## JSON paths

### `located`

```py
@contextmanager
located(path: str, /, *errors: type[Exception]) -> Iterator[None]
```

Add an `at <path>` note to errors of the given types raised in the block, or prefix `path`
onto an existing `at $...` note. Other errors pass through unchanged.

### `index_path`

```py
index_path(path: str, index: int, /) -> str  # "$.a", 2 -> "$.a[2]"
```

### `key_path`

```py
key_path(path: str, key: str, /) -> str  # "$.a", "b" -> "$.a.b"
```

Guide: [JSON-path errors](../guide/paths.md).

## Exceptions

`PyvocabularyError`, `NameDoesNotExistError`, `NameAlreadyRegisteredError`,
`InvalidNameError`: see [Exceptions](exceptions.md).
