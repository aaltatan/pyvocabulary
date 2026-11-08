"""A vocabulary: the named building blocks a JSON-definable language understands.

A rules registry, a steps registry and a formulas registry are all the same
thing underneath: names mapped to entries, some of them hidden from lookups.
`Vocabulary` is that shared part. Packages keep their own decorators on top.
"""

from collections.abc import Callable, Iterable, Iterator, Mapping

from .exceptions import NameAlreadyRegisteredError, NameDoesNotExistError
from .names import InvalidNameErrorFactory, validate_name

type DoesNotExistErrorFactory = Callable[[str, Iterable[str]], Exception]
type AlreadyRegisteredErrorFactory = Callable[[str], Exception]


class Vocabulary[F](Mapping[str, F]):
    """A read-only mapping of visible names to entries, filled with `add`.

    Hidden entries are kept, so a name cannot be reused, but they are left out of
    lookups, iteration and length. That keeps them out of compilers and JSON
    Schemas while the objects stay usable from Python.

    Args:
        kind: What the entries are ("rule", "step"), used in default error messages.
        does_not_exist: Builds the error for an unknown name from the name and
            the visible names. Defaults to `NameDoesNotExistError`.
        already_registered: Builds the error for a duplicate name. Defaults to
            `NameAlreadyRegisteredError`.
        invalid_name: Builds the error for a name that is not an identifier.
            Defaults to `InvalidNameError`.

    Example:
    ```python
    >>> steps = Vocabulary[str]("step")
    >>> steps.add("click", "click()")
    'click()'
    >>> steps.add("debug", "debug()", hidden=True)
    'debug()'
    >>> list(steps), "debug" in steps, len(steps)
    (['click'], False, 1)
    >>> steps["fill"]
    Traceback (most recent call last):
    ...
    pyvocabulary.exceptions.NameDoesNotExistError: Step 'fill' does not exist. ...

    ```

    """

    __slots__ = (
        "_already_registered",
        "_does_not_exist",
        "_entries",
        "_hidden",
        "_invalid_name",
        "_kind",
    )

    def __init__(
        self,
        kind: str = "name",
        /,
        *,
        does_not_exist: DoesNotExistErrorFactory | None = None,
        already_registered: AlreadyRegisteredErrorFactory | None = None,
        invalid_name: InvalidNameErrorFactory | None = None,
    ) -> None:
        self._kind = kind
        self._entries: dict[str, F] = {}
        self._hidden: set[str] = set()
        self._does_not_exist = does_not_exist or (
            lambda name, available: NameDoesNotExistError(name, available, kind=kind)
        )
        self._already_registered = already_registered or (
            lambda name: NameAlreadyRegisteredError(name, kind=kind)
        )
        self._invalid_name = invalid_name

    def add(self, name: str, entry: F, /, *, hidden: bool = False) -> F:
        """Register `entry` under `name` and return the entry.

        Raises:
            InvalidNameError: If `name` is not a valid identifier (or the injected error).
            NameAlreadyRegisteredError: If `name` is taken, hidden or not (or the injected error).

        """
        validate_name(name, kind=self._kind, error=self._invalid_name)

        if name in self._entries:
            raise self._already_registered(name)

        self._entries[name] = entry
        if hidden:
            self._hidden.add(name)

        return entry

    def is_registered(self, name: str, /) -> bool:
        """Whether `name` is taken, including hidden entries.

        Example:
        ```python
        >>> vocabulary = Vocabulary[int]()
        >>> _ = vocabulary.add("secret", 1, hidden=True)
        >>> vocabulary.is_registered("secret"), "secret" in vocabulary
        (True, False)

        ```

        """
        return name in self._entries

    def __getitem__(self, name: str, /) -> F:
        if name not in self:
            raise self._does_not_exist(name, list(self))
        return self._entries[name]

    def get(self, name: str, default: F | None = None, /) -> F | None:  # type: ignore[override]
        # `Mapping.get` only catches `KeyError`; injected errors may be any `LookupError`.
        return self._entries[name] if name in self else default

    def __contains__(self, name: object, /) -> bool:
        return name in self._entries and name not in self._hidden

    def __iter__(self) -> Iterator[str]:
        return (name for name in self._entries if name not in self._hidden)

    def __len__(self) -> int:
        return len(self._entries) - len(self._hidden)

    def __repr__(self) -> str:
        return f"Vocabulary[{self._kind}]({', '.join(self)})"
