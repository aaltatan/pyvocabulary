from typing import Annotated, Literal

import pytest
from pyargprocessors import Process

from pyvocabulary import Choices, Label, Vocabulary, call_json_schema, json_schema_of, labelled

AGE = {"en": "Age", "ar": "العمر"}


class TestLabelled:
    def test_adds_label_and_description(self):
        schema = labelled({"type": "integer"}, label=AGE, description="Years since birth")

        assert schema == {
            "type": "integer",
            "x-label": AGE,
            "x-description": "Years since birth",
        }

    def test_leaves_out_what_is_not_given(self):
        assert labelled({"type": "integer"}) == {"type": "integer"}

    def test_does_not_change_the_given_schema(self):
        schema = {"type": "integer"}

        labelled(schema, label="Age")

        assert schema == {"type": "integer"}

    def test_copies_a_language_map(self):
        label = {"en": "Age"}

        schema = labelled({}, label=label)
        label["en"] = "changed"

        assert schema["x-label"] == {"en": "Age"}

    @pytest.mark.parametrize("label", ["", {}, {"en": 1}, {1: "Age"}, {"en": ""}, 5])
    def test_rejects_invalid_text(self, label):
        with pytest.raises(TypeError, match="label"):
            labelled({}, label=label)


class TestAnnotatedMarkers:
    def test_label_marker(self):
        schema = json_schema_of(Annotated[int, Label(AGE, description="In years")])

        assert schema == {"type": "integer", "x-label": AGE, "x-description": "In years"}

    def test_choices_marker_adds_enum_and_inline_labels(self):
        tier = Annotated[str, Choices({"gold": {"en": "Gold", "ar": "ذهبي"}, "silver": "Silver"})]

        assert json_schema_of(tier) == {
            "type": "string",
            "enum": ["gold", "silver"],
            "x-choices": [
                {"value": "gold", "label": {"en": "Gold", "ar": "ذهبي"}},
                {"value": "silver", "label": "Silver"},
            ],
        }

    def test_choices_on_a_literal_keep_its_enum(self):
        schema = json_schema_of(Annotated[Literal[1, 2], Choices({1: "One", 2: "Two"})])

        assert schema["enum"] == [1, 2]
        assert schema["x-choices"] == [{"value": 1, "label": "One"}, {"value": 2, "label": "Two"}]

    def test_markers_combine_with_process(self):
        schema = json_schema_of(Annotated[int, Process(int), Label("Count")])

        assert schema["x-label"] == "Count"

    def test_empty_choices_are_rejected(self):
        with pytest.raises(ValueError, match="at least one choice"):
            Choices({})

    def test_invalid_choice_label_is_rejected(self):
        with pytest.raises(TypeError, match="label"):
            Choices({"gold": 1})  # type: ignore[dict-item]


class TestCallJsonSchemaLabels:
    def test_call_and_arguments_carry_labels(self):
        def age__ge(value: Annotated[int, Label("Minimum")]) -> bool:
            return True

        schema = call_json_schema("age__ge", age__ge, label=AGE)

        assert schema["x-label"] == AGE
        assert schema["properties"]["args"]["prefixItems"] == [
            {"type": "integer", "x-label": "Minimum"}
        ]

    def test_no_label_by_default(self):
        def is_admin() -> bool:
            return True

        assert "x-label" not in call_json_schema("is_admin", is_admin)


class TestVocabularyLabels:
    def test_labels_of_visible_entries(self):
        rules = Vocabulary[int]("rule")
        rules.add("age__ge", 1, label=AGE)
        rules.add("is_admin", 2)
        rules.add("secret", 3, hidden=True, label="Secret")

        assert rules.labels == {"age__ge": AGE}

    def test_labels_are_a_copy(self):
        rules = Vocabulary[int]("rule")
        rules.add("age__ge", 1, label="Age")

        rules.labels["age__ge"] = "changed"

        assert rules.labels == {"age__ge": "Age"}

    def test_invalid_label_is_rejected_before_adding(self):
        rules = Vocabulary[int]("rule")

        with pytest.raises(TypeError, match="label"):
            rules.add("age__ge", 1, label="")

        assert not rules.is_registered("age__ge")
