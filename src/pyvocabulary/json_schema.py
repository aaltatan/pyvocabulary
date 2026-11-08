"""Generate JSON Schemas from Python type annotations and building-block signatures.

A building block (a rule, a step, a formula variable) is called from JSON as
`{"name": ..., "args": [...], "kwargs": {...}}`. Its signature already says what
those may contain, so the schema is derived from it instead of written by hand.
"""

from collections.abc import Callable, Mapping
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from inspect import Parameter, get_annotations, signature
from types import NoneType, UnionType
from typing import (
    Annotated,
    Any,
    Literal,
    NotRequired,
    Required,
    TypeAliasType,
    Union,
    get_args,
    get_origin,
    is_typeddict,
)
from uuid import UUID

from pyargprocessors import Process, annotated_metadata, input_annotation, resolved_annotations

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

_SCALAR_SCHEMAS: dict[Any, dict[str, Any]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    Decimal: {"type": "number"},
    bool: {"type": "boolean"},
    None: {"type": "null"},
    NoneType: {"type": "null"},
    datetime: {"type": "string", "format": "date-time"},
    date: {"type": "string", "format": "date"},
    time: {"type": "string", "format": "time"},
    UUID: {"type": "string", "format": "uuid"},
}

_ARRAY_TYPES = (list, tuple, set, frozenset)
_WRAPPER_ORIGINS = (Annotated, Required, NotRequired)
_POSITIONAL_KINDS = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
_KEYWORD_KINDS = (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)


def json_schema_of(annotation: Any) -> dict[str, Any]:
    """Return the JSON Schema of a Python type annotation.

    Unknown or unannotated types map to `{}`, which accepts any value. A type
    marked with `Process(fn)` is described by what `fn` accepts, because that is
    what the JSON has to send.

    Example:
    ```python
    >>> json_schema_of(int)
    {'type': 'integer'}
    >>> json_schema_of(list[str])
    {'type': 'array', 'items': {'type': 'string'}}
    >>> json_schema_of(Literal["active", "pending"])
    {'enum': ['active', 'pending'], 'type': 'string'}
    >>> json_schema_of(int | None)
    {'anyOf': [{'type': 'integer'}, {'type': 'null'}]}

    ```

    """
    origin = get_origin(annotation)

    if is_typeddict(annotation):
        return _typeddict_schema(annotation)

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return _enum_schema([member.value for member in annotation])

    if isinstance(annotation, TypeAliasType):
        return json_schema_of(annotation.__value__)

    if origin in _WRAPPER_ORIGINS:
        return json_schema_of(_sent_annotation(annotation))

    if origin is Literal:
        return _enum_schema(list(get_args(annotation)))

    if origin in (Union, UnionType):
        return {"anyOf": [json_schema_of(arg) for arg in get_args(annotation)]}

    if (origin or annotation) in _ARRAY_TYPES:
        return _array_schema(get_args(annotation))

    if (origin or annotation) is dict:
        return _dict_schema(get_args(annotation))

    return dict(_SCALAR_SCHEMAS.get(annotation, {}))


def call_json_schema(
    name: str,
    factory: Callable[..., Any],
    /,
    *,
    extra_properties: Mapping[str, dict[str, Any]] | None = None,
    required: tuple[str, ...] = ("name",),
) -> dict[str, Any]:
    """Return the JSON Schema of one call: `{"name": ..., "args": [...], "kwargs": {...}}`.

    `factory` is a building-block factory whose signature excludes the subject.
    Positional parameters are described under `args` (via `prefixItems`),
    keyword-capable ones under `kwargs`, and the docstring becomes the description.

    Args:
        name: The registered name, fixed with `const`.
        factory: The factory whose signature describes the arguments.
        extra_properties: More keys a package adds to its call shape,
            e.g. `{"inverse": {"type": "boolean"}}` for rules.
        required: The keys that must be present.

    Example:
    ```python
    >>> def age__between(min_age: int, max_age: int = 120) -> bool:
    ...     '''Whether the age is within a range.'''
    ...     return True
    >>> schema = call_json_schema("age__between", age__between)
    >>> schema["properties"]["name"]
    {'const': 'age__between'}
    >>> schema["properties"]["args"]["prefixItems"]
    [{'type': 'integer'}, {'type': 'integer', 'default': 120}]
    >>> schema["description"], schema["required"]
    ('Whether the age is within a range.', ['name'])

    ```

    """
    parameters = list(signature(factory).parameters.values())
    annotations = resolved_annotations(factory)

    def parameter_schema(parameter: Parameter) -> dict[str, Any]:
        schema = json_schema_of(annotations.get(parameter.name, Any))

        if parameter.default is not Parameter.empty and _is_json_value(parameter.default):
            schema["default"] = parameter.default

        return schema

    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "name": {"const": name},
            "args": _args_schema(parameters, parameter_schema),
            "kwargs": _kwargs_schema(parameters, parameter_schema),
            **(extra_properties or {}),
        },
        "required": list(required),
        "additionalProperties": False,
    }

    if factory.__doc__:
        schema["description"] = factory.__doc__.strip()

    return schema


# -----------------------
# helpers
# -----------------------


def _args_schema(
    parameters: list[Parameter],
    parameter_schema: Callable[[Parameter], dict[str, Any]],
) -> dict[str, Any]:
    positional = [parameter for parameter in parameters if parameter.kind in _POSITIONAL_KINDS]
    var_positional = next(
        (parameter for parameter in parameters if parameter.kind is Parameter.VAR_POSITIONAL),
        None,
    )
    prefix_items = [parameter_schema(parameter) for parameter in positional]
    return {
        "type": "array",
        # draft 2020-12 requires `prefixItems` to be non-empty, so it is left out when unused
        **({"prefixItems": prefix_items} if prefix_items else {}),
        "items": parameter_schema(var_positional) if var_positional else False,
    }


def _kwargs_schema(
    parameters: list[Parameter],
    parameter_schema: Callable[[Parameter], dict[str, Any]],
) -> dict[str, Any]:
    keyword = [parameter for parameter in parameters if parameter.kind in _KEYWORD_KINDS]
    var_keyword = next(
        (parameter for parameter in parameters if parameter.kind is Parameter.VAR_KEYWORD),
        None,
    )
    return {
        "type": "object",
        "properties": {parameter.name: parameter_schema(parameter) for parameter in keyword},
        "required": [
            parameter.name
            for parameter in keyword
            if parameter.kind is Parameter.KEYWORD_ONLY and parameter.default is Parameter.empty
        ],
        "additionalProperties": parameter_schema(var_keyword) if var_keyword else False,
    }


def _enum_schema(values: list[Any]) -> dict[str, Any]:
    schema: dict[str, Any] = {"enum": values}

    if values and all(isinstance(value, str) for value in values):
        schema["type"] = "string"

    return schema


def _array_schema(args: tuple[Any, ...]) -> dict[str, Any]:
    return {"type": "array", "items": json_schema_of(args[0]) if args else {}}


def _dict_schema(args: tuple[Any, ...]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": json_schema_of(args[1]) if args else {}}


def _typeddict_schema(annotation: Any) -> dict[str, Any]:
    annotations = get_annotations(annotation)
    return {
        "type": "object",
        "properties": {name: json_schema_of(typ) for name, typ in annotations.items()},
        "required": [name for name in annotations if name in annotation.__required_keys__],
    }


def _sent_annotation(annotation: Any) -> Any:
    """Return the type the JSON must send for an `Annotated`/`Required`/`NotRequired` type."""
    processor = next(
        (item for item in annotated_metadata(annotation) if isinstance(item, Process)), None
    )
    sent = input_annotation(processor) if processor else None
    return get_args(annotation)[0] if sent is None else sent


def _is_json_value(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool | list | dict)
