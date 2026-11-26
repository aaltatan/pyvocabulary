# Type mapping

How `json_schema_of` (and so `call_json_schema`) describes each annotation.

| Annotation | JSON Schema |
| --- | --- |
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float`, `Decimal` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `None` | `{"type": "null"}` |
| `datetime` | `{"type": "string", "format": "date-time"}` |
| `date` | `{"type": "string", "format": "date"}` |
| `time` | `{"type": "string", "format": "time"}` |
| `UUID` | `{"type": "string", "format": "uuid"}` |
| `list[X]`, `tuple[X, ...]`, `set[X]`, `frozenset[X]` | `{"type": "array", "items": <X>}` (the first type argument; `{}` when bare) |
| `dict[K, V]` | `{"type": "object", "additionalProperties": <V>}` (`{}` when bare) |
| `X \| Y`, `Union[X, Y]`, `Optional[X]` | `{"anyOf": [<X>, <Y>]}` |
| `Literal[a, b]` | `{"enum": [a, b]}`, plus `"type": "string"` when every value is a string |
| `Enum` subclass | `{"enum": [member values]}`, plus `"type": "string"` when every value is a string |
| `TypedDict` | `{"type": "object", "properties": {...}, "required": [...]}` |
| `type Alias = X` | the schema of `X` |
| `Annotated[X, ...]` | the schema of `X`, then each `Label` / `Choices` marker applied in order |
| `Annotated[X, Process(fn)]` | the schema of what `fn` accepts, then the markers |
| `Required[X]`, `NotRequired[X]` | the schema of `X` |
| anything else, or no annotation | `{}` (accepts any value) |

```python
from datetime import datetime, time
from enum import Enum
from typing import Annotated, Any
from uuid import UUID

from pyvocabulary import Choices, Label, json_schema_of


class Status(Enum):
    ACTIVE = "active"
    PENDING = "pending"


assert json_schema_of(datetime) == {"type": "string", "format": "date-time"}
assert json_schema_of(time) == {"type": "string", "format": "time"}
assert json_schema_of(UUID) == {"type": "string", "format": "uuid"}
assert json_schema_of(None) == {"type": "null"}
assert json_schema_of(tuple[int, ...]) == {"type": "array", "items": {"type": "integer"}}
assert json_schema_of(list) == {"type": "array", "items": {}}
assert json_schema_of(Status) == {"enum": ["active", "pending"], "type": "string"}
assert json_schema_of(Any) == {}

assert json_schema_of(Annotated[str, Label("Status"), Choices({"active": "Active"})]) == {
    "type": "string",
    "x-label": "Status",
    "enum": ["active"],
    "x-choices": [{"value": "active", "label": "Active"}],
}
```
