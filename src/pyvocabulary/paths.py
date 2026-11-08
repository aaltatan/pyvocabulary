"""Point errors at the part of a JSON definition that caused them.

Compilers walk nested definitions; an error deep inside should say where it
happened, e.g. `at $.expressions[1]`. The location is added as an exception
note, so the original message and type stay unchanged.
"""

from collections.abc import Iterator
from contextlib import contextmanager


def index_path(path: str, index: int, /) -> str:
    """Return the JSON path of an item in a list.

    Example:
    ```python
    >>> index_path("$.branches", 2)
    '$.branches[2]'

    ```

    """
    return f"{path}[{index}]"


def key_path(path: str, key: str, /) -> str:
    """Return the JSON path of a key in an object.

    Example:
    ```python
    >>> key_path(index_path("$.branches", 0), "when")
    '$.branches[0].when'

    ```

    """
    return f"{path}.{key}"


@contextmanager
def located(path: str, /, *errors: type[Exception]) -> Iterator[None]:
    """Add an `at <path>` note to errors of the given types raised inside the block.

    Paths nest: when the error already carries a location from an inner block,
    or from another compiler that reports paths relative to its own root (`$`),
    the outer path is prefixed to it. So a rule compiled inside a decision
    reports its full path in the outer document.

    Example:
    ```python
    >>> try:
    ...     with located("$.branches[1].when", KeyError):
    ...         with located("$.expressions[0]", KeyError):
    ...             raise KeyError("itemz__ge")
    ... except KeyError as error:
    ...     error.__notes__
    ['at $.branches[1].when.expressions[0]']

    ```

    """
    try:
        yield
    except errors as error:
        notes = getattr(error, "__notes__", [])
        index = next((i for i, note in enumerate(notes) if note.startswith(_PREFIX)), None)

        if index is None:
            error.add_note(f"at {path}")
        else:
            notes[index] = f"at {path}{notes[index].removeprefix(_PREFIX)}"

        raise


_PREFIX = "at $"
