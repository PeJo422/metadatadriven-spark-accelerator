from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class ModelValidationError(Exception):
    """Raised when a YAML model does not conform to the schema."""


def load_yaml(model_path: Path) -> dict[str, Any]:
    with model_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ModelValidationError("YAML root must be an object.")

    return data


def validate_model(model: dict[str, Any], schema_path: Path) -> None:
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(model), key=lambda err: list(err.path))

    if not errors:
        return

    formatted_errors = []
    for error in errors:
        path = ".".join(str(p) for p in error.path) or "<root>"
        formatted_errors.append(f"- {path}: {error.message}")

    raise ModelValidationError(
        "Model validation failed:\n" + "\n".join(formatted_errors)
    )
