from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from setupvault.validation.compatibility import check_compatibility
from setupvault.validation.rules import validate_semantic
from setupvault.validation.schema import validate_against_schema


@dataclass
class ValidationReport:
    path: Path
    valid: bool
    schema_errors: list[str] = field(default_factory=list)
    semantic_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def all_errors(self) -> list[str]:
        return self.schema_errors + self.semantic_errors


def validate_snapshot(path: Path) -> ValidationReport:
    """Validate a snapshot file against all layers.

    Reads the raw JSON file and validates without converting to a Snapshot
    object, allowing detection of structural issues that would prevent parsing.

    Args:
        path: Path to the snapshot JSON file.

    Returns:
        A validation report.
    """
    try:
        raw = path.read_bytes()
        data: dict[str, Any] = json.loads(raw)
    except FileNotFoundError:
        return ValidationReport(
            path=path,
            valid=False,
            schema_errors=[f"File not found: {path}"],
        )
    except json.JSONDecodeError as exc:
        return ValidationReport(
            path=path,
            valid=False,
            schema_errors=[f"Invalid JSON: {exc}"],
        )

    schema_errors = validate_against_schema(data)
    semantic_errors = validate_semantic(data)
    warnings = check_compatibility(data)

    all_ok = not schema_errors and not semantic_errors

    return ValidationReport(
        path=path,
        valid=all_ok,
        schema_errors=schema_errors,
        semantic_errors=semantic_errors,
        warnings=warnings,
    )
