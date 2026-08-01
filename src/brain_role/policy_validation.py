from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from brain_role.errors import ValidationIssue
from brain_role.graph_validation import LAYERS
from brain_role.models import InstanceBundle
from brain_role.public_boundary import inspect_text, is_allowed_reference, is_sensitive_key

P0_CORE = {
    "truth-non-fabrication",
    "safety-security",
    "provenance-no-loss",
    "deterministic-transition",
    "no-higher-layer-override",
}
_SECRET_REF = re.compile(r"^env://[A-Z][A-Z0-9_]{2,127}$")


def _walk(value: Any, pointer: str = "") -> list[tuple[str, str, Any]]:
    found: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            segment = "<sensitive-key>" if inspect_text(key_text) else key_text.replace("~", "~0").replace("/", "~1")
            child_pointer = f"{pointer}/{segment}"
            found.append((str(key), child_pointer, child))
            found.extend(_walk(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_pointer = f"{pointer}/{index}"
            found.append(("", child_pointer, child))
            found.extend(_walk(child, child_pointer))
    return found


def _spec(document: dict[str, Any]) -> dict[str, Any]:
    value = document.get("spec", {})
    return value if isinstance(value, dict) else {}


def _string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def validate_policy(bundle: InstanceBundle) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    p0 = bundle.layers.get("P0")
    if p0 is not None:
        spec = _spec(p0)
        path = bundle.layer_paths["P0"]
        if spec.get("status") != "active" or spec.get("mutability") != "immutable":
            issues.append(ValidationIssue(path, "E_P0_IMMUTABLE", "/spec", "P0 must be active and immutable"))
        core = spec.get("p0Core", [])
        if not isinstance(core, list) or len(core) != len(P0_CORE) or _string_set(core) != P0_CORE:
            issues.append(ValidationIssue(path, "E_P0_CORE", "/spec/p0Core", "P0 minimum core is incomplete"))
        if spec.get("dependencies") != []:
            issues.append(
                ValidationIssue(path, "E_P0_DEPENDENCY", "/spec/dependencies", "P0 cannot depend on another layer")
            )

    for layer_id, document in bundle.layers.items():
        spec = _spec(document)
        path = bundle.layer_paths[layer_id]
        if layer_id != "P0" and spec.get("mutability") != "controlled":
            issues.append(
                ValidationIssue(path, "E_LAYER_MUTABILITY", "/spec/mutability", "P1-P6 must use controlled mutability")
            )
        if spec.get("status") == "reserved" and layer_id not in {"P1", "P3"}:
            issues.append(ValidationIssue(path, "E_RESERVED_LAYER", "/spec/status", "only P1 and P3 may be reserved"))
        change = spec.get("changeControl", {})
        if isinstance(change, dict):
            effective = change.get("effectiveAt")
            try:
                if not isinstance(effective, str):
                    raise ValueError
                datetime.fromisoformat(effective.replace("Z", "+00:00"))
            except ValueError:
                issues.append(
                    ValidationIssue(
                        path,
                        "E_EFFECTIVE_TIME",
                        "/spec/changeControl/effectiveAt",
                        "effectiveAt must be an RFC 3339 timestamp",
                    )
                )

    reserved = {layer_id for layer_id, doc in bundle.layers.items() if _spec(doc).get("status") == "reserved"}
    for path, role in bundle.roles:
        spec = _spec(role)
        writes = _string_set(spec.get("writeLayers"))
        forbidden = _string_set(spec.get("forbiddenLayers"))
        if "P0" in writes:
            issues.append(ValidationIssue(path, "E_ROLE_P0_WRITE", "/spec/writeLayers", "roles cannot write P0"))
        if writes & forbidden:
            issues.append(
                ValidationIssue(path, "E_ROLE_PERMISSION_CONFLICT", "/spec", "write and forbidden layers overlap")
            )
        if writes & reserved:
            issues.append(
                ValidationIssue(
                    path, "E_ROLE_RESERVED_WRITE", "/spec/writeLayers", "roles cannot write reserved layers"
                )
            )
        if spec.get("selfEscalation") is not False or spec.get("escalation") == "self":
            issues.append(
                ValidationIssue(path, "E_ROLE_SELF_ESCALATION", "/spec/escalation", "self-escalation is forbidden")
            )
        unknown = (writes | forbidden | _string_set(spec.get("readLayers"))) - set(LAYERS)
        if unknown:
            issues.append(ValidationIssue(path, "E_ROLE_LAYER_UNKNOWN", "/spec", "role references an unknown layer"))

    if not any(
        _spec(policy).get("denySelfEscalation") is True and "P0" in _string_set(_spec(policy).get("denyRoleWrites"))
        for _, policy in bundle.policies
    ):
        issues.append(
            ValidationIssue(bundle.architecture_path, "E_POLICY_P0", "/policies", "a P0 protection policy is required")
        )

    documents = [
        (bundle.architecture_path, bundle.architecture),
        *[(bundle.layer_paths[k], v) for k, v in bundle.layers.items()],
        *bundle.roles,
        *bundle.policies,
    ]
    if bundle.compile_order_path:
        documents.append((bundle.compile_order_path, bundle.compile_order))
    for path, document in documents:
        for key, pointer, value in _walk(document):
            if key == "secretRef":
                if not isinstance(value, str) or not _SECRET_REF.fullmatch(value):
                    issues.append(
                        ValidationIssue(path, "E_SECRET_REF", pointer, "secretRef must use env://VARIABLE_NAME")
                    )
                continue
            if is_sensitive_key(key) and isinstance(value, str) and not is_allowed_reference(value):
                issues.append(ValidationIssue(path, "E_SECRET_LITERAL", pointer, "literal secret fields are forbidden"))
            if isinstance(value, str) and inspect_text(value):
                issues.append(
                    ValidationIssue(
                        path,
                        "E_PUBLIC_BOUNDARY",
                        pointer,
                        "private path, URL, or credential-like value is forbidden",
                    )
                )
    return issues
