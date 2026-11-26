# Labels and choices

Editors built on these schemas (a form builder, a rule editor) show people words, not names:
"Age" for `age`, "Gold" for `"gold"`. The words travel in the schema as `x-label`,
`x-description` and `x-choices`, which JSON Schema validators ignore.

## `Text`

A text is a string for every language, or a `{language: text}` map:

```python
from pyvocabulary import Text

one: Text = "Minimum age"
many: Text = {"en": "Minimum age", "ar": "أدنى عمر"}
```

Empty strings, empty maps, and maps with non-string or empty values raise `TypeError`
wherever a text is accepted.

## `Label`

An `Annotated` marker that labels an argument, optionally with a description:

```python
from typing import Annotated

from pyvocabulary import Label, call_json_schema, json_schema_of

assert json_schema_of(Annotated[int, Label("Minimum age")]) == {
    "type": "integer",
    "x-label": "Minimum age",
}


def age__ge(
    minimum: Annotated[int, Label({"en": "Minimum age", "ar": "أدنى عمر"}, "In years")],
) -> bool:
    return True


argument = call_json_schema("age__ge", age__ge)["properties"]["args"]["prefixItems"][0]

assert argument == {
    "type": "integer",
    "x-label": {"en": "Minimum age", "ar": "أدنى عمر"},
    "x-description": "In years",
}
```

## `Choices`

An `Annotated` marker that lists the values an argument accepts, each with a label. The
schema gets an `enum` of the values, so validators still enforce them, and `x-choices` with
the labels:

```python
from typing import Annotated

from pyvocabulary import Choices, json_schema_of

Tier = Annotated[str, Choices({"gold": {"en": "Gold", "ar": "ذهبي"}, "silver": "Silver"})]

assert json_schema_of(Tier) == {
    "type": "string",
    "enum": ["gold", "silver"],
    "x-choices": [
        {"value": "gold", "label": {"en": "Gold", "ar": "ذهبي"}},
        {"value": "silver", "label": "Silver"},
    ],
}
```

`Choices({})` raises `ValueError`: there must be at least one choice. `Label` and `Choices`
can be combined in one `Annotated`; they are applied in order.

## Labelling calls and entries

`call_json_schema(..., label=...)` labels a whole call, and `Vocabulary.add(..., label=...)`
keeps a label per entry (see [Vocabularies](vocabulary.md#labels)):

```python
from pyvocabulary import call_json_schema


def tier__eq(value: str) -> bool:
    """Whether the customer is in a tier."""
    return True


schema = call_json_schema("tier__eq", tier__eq, label={"en": "Tier is", "ar": "الفئة هي"})

assert schema["x-label"] == {"en": "Tier is", "ar": "الفئة هي"}
assert schema["description"] == "Whether the customer is in a tier."
```

## `labelled`

`labelled` returns a copy of any schema with `x-label` and `x-description` added when given.
Use it for schema pieces you write yourself:

```python
from pyvocabulary import labelled

schema = {"type": "number"}

assert labelled(schema, label="Salary", description="Before tax") == {
    "type": "number",
    "x-label": "Salary",
    "x-description": "Before tax",
}
assert schema == {"type": "number"}
```
