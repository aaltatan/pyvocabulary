"""Labels and choices for JSON Schemas, in one language or several.

Editors built on these schemas (a form builder, rulify) show people words, not
names: `"Age"` for `age`, `"Gold"` for `"gold"`. The words travel in the schema
as `x-label`, `x-description` and `x-choices`; validators ignore them.

A text is a string for every language, or a `{language: text}` map such as
`{"en": "Age", "ar": "العمر"}`.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

type Text = str | Mapping[str, str]


def labelled(
    schema: Mapping[str, Any],
    /,
    *,
    label: Text | None = None,
    description: Text | None = None,
) -> dict[str, Any]:
    """Return a copy of `schema` with `x-label` and `x-description` added when given.

    Raises:
        TypeError: If a text is empty, or a map with non-string or empty entries.

    Example:
    ```python
    >>> labelled({"type": "integer"}, label={"en": "Age", "ar": "العمر"})
    {'type': 'integer', 'x-label': {'en': 'Age', 'ar': 'العمر'}}

    ```

    """
    result = dict(schema)

    if label is not None:
        result["x-label"] = checked_text(label, "label")

    if description is not None:
        result["x-description"] = checked_text(description, "description")

    return result


@dataclass(frozen=True, slots=True)
class Label:
    """An `Annotated` marker that labels an argument in its JSON Schema.

    Example:
    ```python
    >>> from typing import Annotated
    >>> from pyvocabulary import json_schema_of
    >>> json_schema_of(Annotated[int, Label("Minimum age")])
    {'type': 'integer', 'x-label': 'Minimum age'}

    ```

    """

    label: Text
    description: Text | None = None

    def __post_init__(self) -> None:
        labelled({}, label=self.label, description=self.description)

    def apply(self, schema: Mapping[str, Any], /) -> dict[str, Any]:
        return labelled(schema, label=self.label, description=self.description)


@dataclass(frozen=True, slots=True)
class Choices:
    """An `Annotated` marker that lists the values an argument accepts, each with a label.

    The schema gets an `enum` of the values, so validators still enforce them,
    and `x-choices` with the labels written inline.

    Example:
    ```python
    >>> from typing import Annotated
    >>> from pyvocabulary import json_schema_of
    >>> json_schema_of(Annotated[str, Choices({"gold": "Gold", "silver": "Silver"})])
    {'type': 'string', 'enum': ['gold', 'silver'], 'x-choices': [{'value': 'gold', 'label': 'Gold'}, {'value': 'silver', 'label': 'Silver'}]}

    ```

    """  # noqa: E501

    choices: Mapping[Any, Text]

    def __post_init__(self) -> None:
        if not self.choices:
            msg = "Choices need at least one choice"
            raise ValueError(msg)

        for label in self.choices.values():
            checked_text(label, "choice label")

    def apply(self, schema: Mapping[str, Any], /) -> dict[str, Any]:
        return {
            **schema,
            "enum": list(self.choices),
            "x-choices": [
                {"value": value, "label": checked_text(label, "choice label")}
                for value, label in self.choices.items()
            ],
        }


def checked_text(text: object, what: str, /) -> str | dict[str, str]:
    """Return `text` as a string or a fresh `{language: text}` dict, or raise `TypeError`."""
    if isinstance(text, str) and text:
        return text

    if isinstance(text, Mapping) and text:
        items = list(text.items())  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]

        if all(isinstance(k, str) and isinstance(v, str) and v for k, v in items):
            return dict(items)  # pyright: ignore[reportUnknownArgumentType]

    msg = (
        f"Invalid {what}: {text!r}. Expected a non-empty string "
        "or a non-empty {language: text} map of non-empty strings"
    )
    raise TypeError(msg)
