"""Validate the names of building blocks.

A name ends up in JSON definitions, error messages and reprs, so it is kept to
an ASCII Python identifier: `age__between`, `add_milk`.
"""

import re
from collections.abc import Callable

from .exceptions import InvalidNameError

type InvalidNameErrorFactory = Callable[[object], Exception]

# `fullmatch`, not `match` with `$`: `$` also matches before a trailing newline
_IDENTIFIER = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


def validate_name(
    name: object,
    /,
    *,
    kind: str = "name",
    error: InvalidNameErrorFactory | None = None,
) -> str:
    """Return `name` unchanged if it is a valid ASCII Python identifier.

    Args:
        name: The candidate name.
        kind: What is being named, used in the default error message.
        error: Builds the exception to raise for an invalid name. Defaults to
            `InvalidNameError`, which is also a `ValueError`.

    Raises:
        InvalidNameError: If `name` is invalid and no `error` factory is given.

    Example:
    ```python
    >>> validate_name("add_milk")
    'add_milk'
    >>> validate_name("add-milk", kind="step")
    Traceback (most recent call last):
    ...
    pyvocabulary.exceptions.InvalidNameError: Invalid step name: 'add-milk', ...

    ```

    """
    if isinstance(name, str) and _IDENTIFIER.fullmatch(name):
        return name

    raise (error or (lambda value: InvalidNameError(value, kind=kind)))(name)
