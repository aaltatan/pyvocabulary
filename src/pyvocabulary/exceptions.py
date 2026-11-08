"""Exceptions raised by pyvocabulary.

Packages built on pyvocabulary usually inject their own error classes into a
`Vocabulary` (e.g. `RuleDoesNotExistError`), so these defaults are what callers
see only when nothing is injected.
"""

from collections.abc import Iterable


class PyvocabularyError(Exception):
    """Base class for every exception raised by pyvocabulary."""


class NameDoesNotExistError(PyvocabularyError, LookupError):
    """Raised when a name is not in a vocabulary.

    Example:
    ```python
    >>> str(NameDoesNotExistError("stepz", ["click", "fill"], kind="step"))
    "Step 'stepz' does not exist. Available steps: click, fill"

    ```

    """

    def __init__(self, name: str, available: Iterable[str], /, *, kind: str = "name") -> None:
        names = ", ".join(available) or "(none)"
        super().__init__(f"{kind.capitalize()} '{name}' does not exist. Available {kind}s: {names}")


class NameAlreadyRegisteredError(PyvocabularyError):
    """Raised when a name is registered twice in the same vocabulary."""

    def __init__(self, name: str, /, *, kind: str = "name") -> None:
        super().__init__(f"{kind.capitalize()} '{name}' is already registered.")


class InvalidNameError(PyvocabularyError, ValueError):
    """Raised when a name is not a valid ASCII Python identifier."""

    def __init__(self, name: object, /, *, kind: str = "name") -> None:
        label = "name" if kind == "name" else f"{kind} name"
        super().__init__(
            f"Invalid {label}: {name!r}, "
            "you should follow the python variable naming convention: "
            "name must start with a letter and can only contain letters, numbers and underscores"
        )
