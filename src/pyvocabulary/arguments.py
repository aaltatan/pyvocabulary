"""Classify the `TypeError` raised by `inspect.Signature.bind`.

Building blocks bind their arguments when they are built, so a wrong argument
fails early. Each package maps the problem to its own exception class.
"""

import re
from typing import Literal

type BindProblem = Literal[
    "positional_only",
    "missing",
    "too_many",
    "unexpected_keyword",
    "multiple_values",
]

_PATTERNS: tuple[tuple[str, BindProblem], ...] = (
    (r"positional.only.*passed as (a )?keyword", "positional_only"),
    (r"missing a required", "missing"),
    (r"too many positional arguments", "too_many"),
    (r"got an unexpected keyword argument", "unexpected_keyword"),
    (r"multiple values for argument", "multiple_values"),
)


def bind_problem(error: TypeError, /) -> BindProblem | None:
    """Return what went wrong in a failed `Signature.bind`, or `None` if unknown.

    Example:
    ```python
    >>> bind_problem(TypeError("too many positional arguments"))
    'too_many'
    >>> bind_problem(TypeError("missing a required argument: 'value'"))
    'missing'
    >>> bind_problem(TypeError("something else")) is None
    True

    ```

    """
    message = str(error)
    return next((problem for pattern, problem in _PATTERNS if re.search(pattern, message)), None)
