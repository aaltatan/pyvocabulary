# Reference

- [API](api.md): every public name of `pyvocabulary`.
- [Type mapping](type-mapping.md): how each Python annotation becomes a JSON Schema.
- [Exceptions](exceptions.md): the exception hierarchy and when each one is raised.

Everything is importable from the package root:

```python
import pyvocabulary

assert sorted(pyvocabulary.__all__) == [
    "BindProblem",
    "Choices",
    "InvalidNameError",
    "JSON_SCHEMA_DIALECT",
    "Label",
    "NameAlreadyRegisteredError",
    "NameDoesNotExistError",
    "PyvocabularyError",
    "Text",
    "Vocabulary",
    "bind_problem",
    "call_json_schema",
    "index_path",
    "json_schema_of",
    "key_path",
    "labelled",
    "located",
    "validate_name",
]
```
