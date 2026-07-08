from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMAS_DIR = Path(__file__).parent / "schemas"


def validate_against_schema(data: dict[str, Any]) -> list[str]:
    """Validate a snapshot dict against its declared JSON Schema version.

    Args:
        data: Parsed snapshot dictionary.

    Returns:
        A list of schema violation messages (empty if valid).
    """
    version = data.get("snapshot_version", 1)
    schema_path = _SCHEMAS_DIR / f"snapshot-v{version}.json"

    if not schema_path.exists():
        return [f"No schema found for version {version}"]

    try:
        import jsonschema
    except ImportError:
        return _fallback_validation(data)

    try:
        schema = json.loads(schema_path.read_text())
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        return [_format_jsonschema_error(e) for e in errors]
    except json.JSONDecodeError as exc:
        return [f"Schema file {schema_path} is invalid JSON: {exc}"]


def _format_jsonschema_error(error: Any) -> str:
    path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
    return f"{path}: {error.message}"


def _fallback_validation(data: dict[str, Any]) -> list[str]:
    """Minimal validation when jsonschema is not installed."""
    errors: list[str] = []
    required = ["snapshot_version", "tool_version", "created_at", "system", "packages"]
    for field in required:
        if field not in data:
            errors.append(f"root: '{field}' is a required property")
    return errors
