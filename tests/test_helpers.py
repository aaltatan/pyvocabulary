from inspect import signature

import pytest

from pyvocabulary import (
    InvalidNameError,
    bind_problem,
    index_path,
    key_path,
    located,
    validate_name,
)


class TestValidateName:
    @pytest.mark.parametrize("name", ["a", "_private", "age__between", "A1"])
    def test_valid_name_is_returned(self, name):
        assert validate_name(name) == name

    def test_non_string_is_invalid(self):
        with pytest.raises(InvalidNameError, match=r"^Invalid name: 3, "):
            validate_name(3)

    def test_trailing_newline_is_invalid(self):
        with pytest.raises(InvalidNameError):
            validate_name("name\n")

    def test_custom_error_factory(self):
        with pytest.raises(KeyError):
            validate_name("a-b", error=KeyError)


class TestBindProblem:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("'x' parameter is positional only, but was passed as a keyword", "positional_only"),
            ("missing a required argument: 'value'", "missing"),
            ("too many positional arguments", "too_many"),
            ("got an unexpected keyword argument 'colour'", "unexpected_keyword"),
            ("multiple values for argument 'value'", "multiple_values"),
            ("something else", None),
        ],
    )
    def test_classifies_signature_bind_messages(self, message, expected):
        assert bind_problem(TypeError(message)) == expected

    def test_classifies_a_real_bind_error(self):
        def rule(value: int) -> bool:
            return bool(value)

        with pytest.raises(TypeError) as info:
            signature(rule).bind(1, 2)

        assert bind_problem(info.value) == "too_many"


class TestPaths:
    def test_paths_compose(self):
        assert key_path(index_path(key_path("$", "branches"), 1), "when") == "$.branches[1].when"

    def test_located_adds_a_note(self):
        error = KeyError("x")

        with pytest.raises(KeyError) as info, located("$[2]", KeyError):
            raise error

        assert info.value.__notes__ == ["at $[2]"]

    def test_located_ignores_other_error_types(self):
        error = ValueError("x")

        with pytest.raises(ValueError, match="x") as info, located("$[2]", KeyError):
            raise error

        assert not hasattr(info.value, "__notes__")

    def test_located_prefixes_an_inner_relative_path(self):
        def inner_compiler() -> None:
            error = LookupError("Rule 'x' does not exist")
            error.add_note("at $.expressions[0]")
            raise error

        with pytest.raises(LookupError) as info, located("$.branches[1].when", LookupError):
            inner_compiler()

        assert info.value.__notes__ == ["at $.branches[1].when.expressions[0]"]

    def test_located_keeps_unrelated_notes(self):
        error = KeyError("x")
        error.add_note("hint: check the spelling")

        with pytest.raises(KeyError) as info, located("$", KeyError):
            raise error

        assert info.value.__notes__ == ["hint: check the spelling", "at $"]

    def test_located_without_error_does_nothing(self):
        with located("$", KeyError):
            value = 1

        assert value == 1
