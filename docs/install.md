# Installation

pyvocabulary needs **Python 3.12 or newer**.

=== "uv"

    ```bash
    uv add pyvocabulary
    ```

=== "pip"

    ```bash
    pip install pyvocabulary
    ```

Its only runtime dependency is [pyargprocessors](https://pypi.org/project/pyargprocessors/),
used to describe parameters marked with `Process(fn)` in JSON Schemas.

You rarely install pyvocabulary on its own: pyspecification, pyformula, pyflowstep and
pyruleset pull it in. Install it directly when you build a package of your own in the same
style.

## Check it works

```python
from pyvocabulary import Vocabulary

steps = Vocabulary[str]("step")

steps.add("click", "click()")

assert repr(steps) == "Vocabulary[step](click)"
```

## Development

```bash
uv sync
uv run pytest --cov --cov-branch
uvx ruff check . && uvx ruff format --check .
uvx pyright src
```

Build these docs locally with:

```bash
uv run --with mkdocs-material mkdocs serve
```
