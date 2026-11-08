import re

import pytest

from pyvocabulary import (
    InvalidNameError,
    NameAlreadyRegisteredError,
    NameDoesNotExistError,
    Vocabulary,
)


class RuleDoesNotExistError(LookupError):
    def __init__(self, name, available):
        super().__init__(f"Rule '{name}' does not exist. Available rules: {', '.join(available)}")


class RuleAlreadyRegisteredError(Exception):
    def __init__(self, name):
        super().__init__(f"Rule '{name}' is already registered")


@pytest.fixture
def rules() -> Vocabulary[str]:
    vocabulary = Vocabulary[str]("rule")
    vocabulary.add("is_admin", "is_admin()")
    vocabulary.add("age__gt", "age__gt()")
    vocabulary.add("debug", "debug()", hidden=True)
    return vocabulary


class TestAdding:
    def test_add_returns_the_entry(self):
        assert Vocabulary[int]().add("one", 1) == 1

    def test_duplicate_name_raises(self, rules):
        with pytest.raises(
            NameAlreadyRegisteredError, match="Rule 'is_admin' is already registered"
        ):
            rules.add("is_admin", "again")

    def test_hidden_name_cannot_be_reused(self, rules):
        with pytest.raises(NameAlreadyRegisteredError, match="'debug'"):
            rules.add("debug", "again")

    @pytest.mark.parametrize("name", ["add-milk", "1st", "", "<lambda>", "ñame"])
    def test_invalid_name_raises(self, name):
        with pytest.raises(InvalidNameError, match="Invalid step name"):
            Vocabulary[int]("step").add(name, 1)

    def test_invalid_name_is_a_value_error(self):
        with pytest.raises(ValueError, match="Invalid"):
            Vocabulary[int]().add("a b", 1)


class TestLookup:
    def test_visible_names_in_registration_order(self, rules):
        assert list(rules) == ["is_admin", "age__gt"]

    def test_length_counts_visible_entries(self, rules):
        assert len(rules) == 2

    def test_hidden_entry_is_not_contained(self, rules):
        assert "debug" not in rules
        assert rules.is_registered("debug")

    def test_hidden_entry_cannot_be_looked_up(self, rules):
        with pytest.raises(NameDoesNotExistError):
            rules["debug"]

    def test_unknown_name_lists_available_names(self, rules):
        with pytest.raises(
            NameDoesNotExistError,
            match=re.escape("Rule 'agee__gt' does not exist. Available rules: is_admin, age__gt"),
        ):
            rules["agee__gt"]

    def test_unknown_name_is_a_lookup_error(self, rules):
        with pytest.raises(LookupError):
            rules["nope"]

    def test_empty_vocabulary_says_none(self):
        with pytest.raises(NameDoesNotExistError, match=r"Available names: \(none\)"):
            Vocabulary[int]()["x"]

    def test_mapping_helpers_work(self, rules):
        assert dict(rules) == {"is_admin": "is_admin()", "age__gt": "age__gt()"}
        assert rules.get("nope") is None
        assert rules.get("debug", "fallback") == "fallback"
        assert rules.get("is_admin") == "is_admin()"

    def test_non_string_is_not_contained(self, rules):
        assert 1 not in rules

    def test_repr_shows_kind_and_visible_names(self, rules):
        assert repr(rules) == "Vocabulary[rule](is_admin, age__gt)"


class TestInjectedErrors:
    def test_injected_errors_are_raised(self):
        vocabulary = Vocabulary[int](
            "rule",
            does_not_exist=RuleDoesNotExistError,
            already_registered=RuleAlreadyRegisteredError,
            invalid_name=lambda name: TypeError(f"bad {name}"),
        )
        vocabulary.add("one", 1)

        with pytest.raises(RuleDoesNotExistError, match="Available rules: one"):
            vocabulary["two"]

        with pytest.raises(RuleAlreadyRegisteredError):
            vocabulary.add("one", 1)

        with pytest.raises(TypeError, match="bad a-b"):
            vocabulary.add("a-b", 1)
