from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from brain_role.change_report import ChangeFinding, ChangeReport
from brain_role.compiled_loader import CompiledBundleArtifact, validate_compiled_bundle_document
from brain_role.errors import InputFailure
from brain_role.models import Document


@dataclass(frozen=True, order=True)
class _Version:
    major: int
    minor: int
    patch: int


def _version(value: object) -> _Version:
    if not isinstance(value, str):
        raise InputFailure("compiled bundle metadata version is invalid")
    parts = value.split(".")
    if len(parts) != 3 or parts[0] != "0" or parts[1] != "1":
        raise InputFailure("compiled bundle metadata version is invalid")
    try:
        patch = int(parts[2])
    except ValueError as exc:
        raise InputFailure("compiled bundle metadata version is invalid") from exc
    return _Version(0, 1, patch)


def _instant(value: object) -> datetime:
    if not isinstance(value, str):
        raise InputFailure("compiled bundle changeControl.effectiveAt is invalid")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InputFailure("compiled bundle changeControl.effectiveAt is invalid") from exc
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    return instant.astimezone(UTC)


def _identity(document: Document) -> tuple[str, str, str, str]:
    metadata = document.get("metadata", {})
    if not isinstance(metadata, dict):
        raise InputFailure("compiled bundle metadata is invalid")
    return (
        str(document.get("apiVersion", "")),
        str(metadata.get("architectureId", "")),
        str(metadata.get("id", "")),
        str(metadata.get("classification", "")),
    )


def _metadata_version(document: Document) -> _Version:
    metadata = document.get("metadata", {})
    if not isinstance(metadata, dict):
        raise InputFailure("compiled bundle metadata is invalid")
    return _version(metadata.get("version"))


def _layer_id(layer: Document) -> str:
    spec = layer.get("spec", {})
    if not isinstance(spec, dict):
        return ""
    return str(spec.get("layer", ""))


def _by_layer(document: Document) -> dict[str, Document]:
    layers = document.get("layers", [])
    if not isinstance(layers, list):
        raise InputFailure("compiled bundle layers are invalid")
    result: dict[str, Document] = {}
    for layer in layers:
        if isinstance(layer, dict):
            result[_layer_id(layer)] = layer
    return result


def _by_id(document: Document, key: str) -> dict[str, Document]:
    values = document.get(key, [])
    if not isinstance(values, list):
        raise InputFailure(f"compiled bundle {key} are invalid")
    result: dict[str, Document] = {}
    for value in values:
        if not isinstance(value, dict):
            continue
        metadata = value.get("metadata", {})
        if isinstance(metadata, dict):
            result[str(metadata.get("id", ""))] = value
    return result


def _canonical(document: Document) -> bytes:
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _strip_control_fields(layer: Document) -> Document:
    stripped = copy.deepcopy(layer)
    metadata = stripped.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("version", None)
    spec = stripped.get("spec")
    if isinstance(spec, dict):
        spec.pop("changeControl", None)
    return stripped


def _component_findings(
    component_type: str,
    component_id: str,
    decision: str,
    code: str,
    message: str,
) -> ChangeFinding:
    return ChangeFinding(component_type, component_id, decision, code, message)


def _change_control(layer: Document) -> dict[str, object]:
    spec = layer.get("spec", {})
    value = spec.get("changeControl", {}) if isinstance(spec, dict) else {}
    return value if isinstance(value, dict) else {}


def _compare_layers(baseline: Document, candidate: Document, findings: list[ChangeFinding]) -> bool:
    baseline_layers = _by_layer(baseline)
    candidate_layers = _by_layer(candidate)
    semantic_change = False
    for layer_id, base_layer in baseline_layers.items():
        cand_layer = candidate_layers.get(layer_id)
        if cand_layer is None:
            findings.append(
                _component_findings("layer", layer_id, "deny", "E_CHANGE_LAYER_MISSING", "layer set changed")
            )
            continue
        if layer_id == "brainstem":
            if _canonical(base_layer) != _canonical(cand_layer):
                findings.append(
                    _component_findings(
                        "layer",
                        layer_id,
                        "deny",
                        "E_CHANGE_BRAINSTEM",
                        "brainstem must not change",
                    )
                )
            continue
        if _strip_control_fields(base_layer) == _strip_control_fields(cand_layer):
            if _canonical(base_layer) != _canonical(cand_layer):
                findings.append(
                    _component_findings(
                        "layer",
                        layer_id,
                        "deny",
                        "E_CHANGE_EMPTY_CONTROL_UPDATE",
                        "control metadata changed without a semantic layer update",
                    )
                )
            continue
        semantic_change = True
        if _metadata_version(cand_layer) <= _metadata_version(base_layer):
            findings.append(
                _component_findings(
                    "layer",
                    layer_id,
                    "deny",
                    "E_CHANGE_LAYER_VERSION_NOT_ADVANCED",
                    "controlled layer version must advance when semantics change",
                )
            )
            continue
        base_change_control = _change_control(base_layer)
        cand_change_control = _change_control(cand_layer)
        if _instant(cand_change_control.get("effectiveAt")) <= _instant(base_change_control.get("effectiveAt")):
            findings.append(
                _component_findings(
                    "layer",
                    layer_id,
                    "deny",
                    "E_CHANGE_EFFECTIVE_AT_NOT_ADVANCED",
                    "controlled layer effectiveAt must advance when semantics change",
                )
            )
            continue
        findings.append(
            _component_findings(
                "layer",
                layer_id,
                "allow",
                "OK_CONTROLLED_LAYER_UPDATE",
                "controlled layer semantic change satisfies C3-a structure",
            )
        )
    return semantic_change


def _compare_exact_collection(
    component_type: str,
    baseline_values: dict[str, Document],
    candidate_values: dict[str, Document],
    findings: list[ChangeFinding],
    code: str,
    message: str,
) -> None:
    if set(baseline_values) != set(candidate_values):
        findings.append(_component_findings(component_type, "*", "deny", code, message))
        return
    for component_id in sorted(baseline_values):
        if _canonical(baseline_values[component_id]) != _canonical(candidate_values[component_id]):
            findings.append(_component_findings(component_type, component_id, "deny", code, message))


def compare_compiled_bundles(baseline: CompiledBundleArtifact, candidate: CompiledBundleArtifact) -> ChangeReport:
    validate_compiled_bundle_document(baseline.document)
    validate_compiled_bundle_document(candidate.document)
    findings: list[ChangeFinding] = []
    baseline_identity = _identity(baseline.document)
    candidate_identity = _identity(candidate.document)
    if baseline_identity[0] != candidate_identity[0]:
        findings.append(
            _component_findings(
                "architecture",
                baseline_identity[2],
                "deny",
                "E_CHANGE_API_VERSION_MISMATCH",
                "compiled bundle apiVersion must match",
            )
        )
        return _build_report(baseline, candidate, findings)
    if baseline_identity[1:] != candidate_identity[1:]:
        findings.append(
            _component_findings(
                "architecture",
                candidate_identity[2] or baseline_identity[2] or "*",
                "deny",
                "E_CHANGE_IDENTITY_MISMATCH",
                "architecture identity must remain stable",
            )
        )
        return _build_report(baseline, candidate, findings)

    baseline_compile_order = baseline.document.get("compileOrder", [])
    candidate_compile_order = candidate.document.get("compileOrder", [])
    if baseline_compile_order != candidate_compile_order:
        findings.append(
            _component_findings(
                "compileOrder",
                baseline_identity[2],
                "deny",
                "E_CHANGE_CONTROL_UNAVAILABLE_COMPILE_ORDER",
                "compile order changes are not controlled by C3-a",
            )
        )

    semantic_change = _compare_layers(baseline.document, candidate.document, findings)
    _compare_exact_collection(
        "role",
        _by_id(baseline.document, "roles"),
        _by_id(candidate.document, "roles"),
        findings,
        "E_CHANGE_CONTROL_UNAVAILABLE_ROLE",
        "role changes are not controlled by C3-a",
    )
    _compare_exact_collection(
        "policy",
        _by_id(baseline.document, "policies"),
        _by_id(candidate.document, "policies"),
        findings,
        "E_CHANGE_CONTROL_UNAVAILABLE_POLICY",
        "policy changes are not controlled by C3-a",
    )

    if semantic_change:
        if _metadata_version(candidate.document) <= _metadata_version(baseline.document):
            findings.append(
                _component_findings(
                    "architecture",
                    baseline_identity[2],
                    "deny",
                    "E_CHANGE_VERSION_NOT_ADVANCED",
                    "architecture version must advance when controlled layers change",
                )
            )
    elif _metadata_version(candidate.document) != _metadata_version(baseline.document):
        findings.append(
            _component_findings(
                "architecture",
                baseline_identity[2],
                "deny",
                "E_CHANGE_EMPTY_CONTROL_UPDATE",
                "version-only updates are not valid change reports",
            )
        )

    return _build_report(baseline, candidate, findings)


def _build_report(
    baseline: CompiledBundleArtifact,
    candidate: CompiledBundleArtifact,
    findings: list[ChangeFinding],
) -> ChangeReport:
    api_version = str(candidate.document.get("apiVersion", baseline.document.get("apiVersion", "")))
    baseline_metadata = baseline.document.get("metadata", {})
    candidate_metadata = candidate.document.get("metadata", {})
    baseline_id = str(baseline_metadata.get("id", "")) if isinstance(baseline_metadata, dict) else ""
    candidate_id = str(candidate_metadata.get("id", "")) if isinstance(candidate_metadata, dict) else ""
    baseline_version = str(baseline_metadata.get("version", "")) if isinstance(baseline_metadata, dict) else ""
    candidate_version = str(candidate_metadata.get("version", "")) if isinstance(candidate_metadata, dict) else ""
    architecture_id = str(baseline_metadata.get("architectureId", "")) if isinstance(baseline_metadata, dict) else ""
    allowed = not any(finding.decision == "deny" for finding in findings)
    ordered_findings = tuple(
        sorted(
            findings,
            key=lambda item: (item.component_type, item.component_id, item.code, item.message),
        )
    )
    return ChangeReport(
        api_version=api_version,
        allowed=allowed,
        baseline_sha256=baseline.sha256,
        candidate_sha256=candidate.sha256,
        architecture_id=architecture_id,
        baseline_id=baseline_id,
        baseline_version=baseline_version,
        candidate_id=candidate_id,
        candidate_version=candidate_version,
        findings=ordered_findings,
    )
