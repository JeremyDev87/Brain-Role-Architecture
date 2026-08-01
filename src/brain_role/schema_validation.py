from __future__ import annotations

import json
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker

from brain_role.errors import ValidationIssue
from brain_role.public_boundary import inspect_text

_SCHEMA_BY_KIND = {
    "BrainArchitecture": "architecture.schema.json",
    "LayerManifest": "layer.schema.json",
    "RoleManifest": "role.schema.json",
    "PolicyManifest": "policy.schema.json",
    "CompileOrder": "compile-order.schema.json",
}


def _pointer(parts: Any) -> str:
    encoded = [
        "<sensitive-key>"
        if inspect_text(str(part))
        else str(part).replace("~", "~0").replace("/", "~1")
        for part in parts
    ]
    return "/" + "/".join(encoded) if encoded else ""


@cache
def load_schema(name: str) -> dict[str, Any]:
    package_candidate = resources.files("brain_role").joinpath("schemas", "v1alpha1", name)
    if package_candidate.is_file():
        return cast(
            dict[str, Any],
            json.loads(package_candidate.read_text(encoding="utf-8")),
        )
    source_candidate = Path(__file__).resolve().parents[2] / "schemas" / "v1alpha1" / name
    return cast(
        dict[str, Any],
        json.loads(source_candidate.read_text(encoding="utf-8")),
    )


def validate_document(document: dict[str, Any], path: str) -> list[ValidationIssue]:
    kind = document.get("kind")
    if not isinstance(kind, str):
        return [ValidationIssue(path, "E_KIND", "/kind", "unsupported document kind")]
    schema_name = _SCHEMA_BY_KIND.get(kind)
    if schema_name is None:
        return [ValidationIssue(path, "E_KIND", "/kind", "unsupported document kind")]
    validator = Draft202012Validator(load_schema(schema_name), format_checker=FormatChecker())
    issues = [
        ValidationIssue(
            path,
            "E_SCHEMA",
            _pointer(error.absolute_path),
            "document does not conform to schema",
        )
        for error in validator.iter_errors(document)
    ]
    return sorted(issues)
