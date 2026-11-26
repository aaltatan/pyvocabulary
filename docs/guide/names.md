# Names

Names end up in JSON, error messages and reprs, so they are ASCII Python identifiers:
a letter or `_`, then letters, digits or `_`. `validate_name` returns the name unchanged or
raises. Every `Vocabulary.add` calls it.

```python
from pyvocabulary import InvalidNameError, validate_name

assert validate_name("add_milk") == "add_milk"
assert validate_name("_private") == "_private"

for bad in ("add-milk", "1st", "é", "", "add_milk\n", 42):
    try:
        validate_name(bad)
    except InvalidNameError:
        pass
    else:
        raise AssertionError(bad)
```

A trailing newline is rejected: the check uses `re.fullmatch`, not `match` with `$`.

## The message

`kind` names what is being validated:

```python
from pyvocabulary import InvalidNameError, validate_name

try:
    validate_name(42, kind="formula")
except InvalidNameError as error:
    assert str(error) == (
        "Invalid formula name: 42, "
        "you should follow the python variable naming convention: "
        "name must start with a letter and can only contain letters, numbers and underscores"
    )
```

## Your own error

`error` builds the exception from the rejected name. `InvalidNameError` is also a
`ValueError`, but an injected error can be anything:

```python
from pyvocabulary import validate_name

try:
    validate_name("é", error=lambda name: KeyError(name))
except KeyError as error:
    assert error.args == ("é",)
```
