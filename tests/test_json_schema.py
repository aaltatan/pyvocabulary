from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal, NotRequired, Required, TypedDict
from uuid import UUID

import pytest
from pyargprocessors import Process

from pyvocabulary import JSON_SCHEMA_DIALECT, call_json_schema, json_schema_of


class Color(Enum):
    RED = "red"
    BLUE = "blue"


class Movie(TypedDict):
    title: Required[str]
    year: NotRequired[int]


type Score = int


def to_decimal(value: str) -> Decimal:
    return Decimal(value)


class TestJsonSchemaOf:
    @pytest.mark.parametrize(
        ("annotation", "expected"),
        [
            (str, {"type": "string"}),
            (int, {"type": "integer"}),
            (float, {"type": "number"}),
            (Decimal, {"type": "number"}),
            (bool, {"type": "boolean"}),
            (None, {"type": "null"}),
            (datetime, {"type": "string", "format": "date-time"}),
            (date, {"type": "string", "format": "date"}),
            (time, {"type": "string", "format": "time"}),
            (UUID, {"type": "string", "format": "uuid"}),
            (Any, {}),
            (object, {}),
        ],
    )
    def test_scalars(self, annotation, expected):
        assert json_schema_of(annotation) == expected

    def test_containers(self):
        assert json_schema_of(list) == {"type": "array", "items": {}}
        assert json_schema_of(tuple[int, ...]) == {"type": "array", "items": {"type": "integer"}}
        assert json_schema_of(dict[str, bool]) == {
            "type": "object",
            "additionalProperties": {"type": "boolean"},
        }
        assert json_schema_of(dict) == {"type": "object", "additionalProperties": {}}

    def test_enum_and_literal(self):
        assert json_schema_of(Color) == {"enum": ["red", "blue"], "type": "string"}
        assert json_schema_of(Literal[1, 2]) == {"enum": [1, 2]}

    def test_union(self):
        assert json_schema_of(int | str) == {"anyOf": [{"type": "integer"}, {"type": "string"}]}

    def test_type_alias(self):
        assert json_schema_of(Score) == {"type": "integer"}

    def test_typeddict(self):
        assert json_schema_of(Movie) == {
            "type": "object",
            "properties": {"title": {"type": "string"}, "year": {"type": "integer"}},
            "required": ["title"],
        }

    def test_annotated_without_processor_uses_the_inner_type(self):
        assert json_schema_of(Annotated[int, "meta"]) == {"type": "integer"}

    def test_processor_describes_what_json_sends(self):
        assert json_schema_of(Annotated[Decimal, Process(to_decimal)]) == {"type": "string"}


class TestCallJsonSchema:
    def test_positional_and_keyword_parameters(self):
        def between(low: int, high: int = 10, *, inclusive: bool = True) -> bool:
            return True

        schema = call_json_schema("between", between)

        assert schema["properties"]["args"] == {
            "type": "array",
            "prefixItems": [{"type": "integer"}, {"type": "integer", "default": 10}],
            "items": False,
        }
        assert schema["properties"]["kwargs"]["properties"]["inclusive"] == {
            "type": "boolean",
            "default": True,
        }
        assert schema["properties"]["kwargs"]["required"] == []
        assert "description" not in schema

    def test_required_keyword_only_parameter(self):
        def tagged(*, tag: str) -> bool:
            return True

        schema = call_json_schema("tagged", tagged)

        assert schema["properties"]["kwargs"]["required"] == ["tag"]

    def test_var_args_and_var_kwargs(self):
        def anything(*values: int, **options: str) -> bool:
            return True

        schema = call_json_schema("anything", anything)

        assert schema["properties"]["args"]["items"] == {"type": "integer"}
        assert schema["properties"]["kwargs"]["additionalProperties"] == {"type": "string"}

    def test_non_json_default_is_left_out(self):
        def dated(when: date = date(2026, 1, 1)) -> bool:
            return True

        schema = call_json_schema("dated", dated)

        assert schema["properties"]["args"]["prefixItems"] == [{"type": "string", "format": "date"}]

    def test_extra_properties_and_required(self):
        def is_admin() -> bool:
            """Whether the user is an admin."""
            return True

        schema = call_json_schema(
            "is_admin",
            is_admin,
            extra_properties={"inverse": {"type": "boolean"}},
            required=("name", "args", "kwargs", "inverse"),
        )

        assert schema["properties"]["inverse"] == {"type": "boolean"}
        assert schema["required"] == ["name", "args", "kwargs", "inverse"]
        assert schema["description"] == "Whether the user is an admin."


def test_dialect_is_draft_2020_12():
    assert JSON_SCHEMA_DIALECT.endswith("2020-12/schema")
