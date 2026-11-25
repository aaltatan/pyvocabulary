"""pyvocabulary: the shared core of composable, JSON-definable building blocks.

Used by pyspecification, pyflowstep and pyruleset for the parts every such
package needs: a registry of named entries, JSON Schemas generated from
signatures, errors that point at a JSON path, and early argument checks.
"""

from .arguments import BindProblem, bind_problem
from .exceptions import (
    InvalidNameError,
    NameAlreadyRegisteredError,
    NameDoesNotExistError,
    PyvocabularyError,
)
from .json_schema import JSON_SCHEMA_DIALECT, call_json_schema, json_schema_of
from .labels import Choices, Label, Text, labelled
from .names import validate_name
from .paths import index_path, key_path, located
from .vocabulary import Vocabulary

__all__ = [
    "JSON_SCHEMA_DIALECT",
    "BindProblem",
    "Choices",
    "InvalidNameError",
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
