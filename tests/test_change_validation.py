from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from brain_role.change_report import json_report
from brain_role.change_validation import compare_compiled_bundles
from brain_role.compiled_loader import load_compiled_bundle
from brain_role.compiler import compile_bundle, write_compiled_bundle
from brain_role.errors import InputFailure
from brain_role.loader import MAX_FILE_BYTES, MAX_NESTING_DEPTH
from brain_role.schema_validation import validate_document
from brain_role.validator import validate_instance


def _compiled_document(anatomical_example_root: Path) -> dict[str, Any]:
    validated = validate_instance(anatomical_example_root)
    assert validated.valid and validated.bundle is not None
    return compile_bundle(validated.bundle)


def _artifact(tmp_path: Path, name: str, document: dict[str, Any]):
    target = tmp_path / name
    write_compiled_bundle(document, target)
    return load_compiled_bundle(target)


def _bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def _find_by_component(collection: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for item in collection:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        if isinstance(metadata, dict) and key == "metadata.id" and metadata.get("id") == value:
            return item
        if isinstance(spec, dict) and key == "spec.layer" and spec.get("layer") == value:
            return item
    raise AssertionError(f"missing component {key}={value}")


def _run_diff_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "brain_role", "diff", *args],
        text=True,
        capture_output=True,
        check=False,
    )


def _write_raw(path: Path, payload: bytes) -> Path:
    path.write_bytes(payload)
    return path


def _canonical_json(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def test_load_compiled_bundle_rejects_noncanonical_input_and_symlink(
    anatomical_example_root: Path,
    tmp_path: Path,
) -> None:
    document = _compiled_document(anatomical_example_root)
    canonical = tmp_path / "canonical.json"
    write_compiled_bundle(document, canonical)

    pretty = tmp_path / "pretty.json"
    pretty.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(InputFailure):
        load_compiled_bundle(pretty)

    symlink = tmp_path / "link.json"
    symlink.symlink_to(canonical)
    with pytest.raises(InputFailure):
        load_compiled_bundle(symlink)

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    nested = real_parent / "nested.json"
    write_compiled_bundle(document, nested)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(InputFailure):
        load_compiled_bundle(linked_parent / "nested.json")


def test_load_compiled_bundle_rejects_malformed_duplicate_nonfinite_deep_secret_and_oversized(
    anatomical_example_root: Path,
    tmp_path: Path,
) -> None:
    document = _compiled_document(anatomical_example_root)
    baseline = tmp_path / "baseline.json"
    write_compiled_bundle(document, baseline)

    nested: dict[str, Any] = {}
    cursor = nested
    for _ in range(MAX_NESTING_DEPTH + 2):
        child: dict[str, Any] = {}
        cursor["nested"] = child
        cursor = child

    secret = "ghp_" + "A" * 24
    secret_document = copy.deepcopy(document)
    secret_document["metadata"]["id"] = secret
    rejected = {
        "malformed.json": b"{",
        "duplicate.json": b'{"apiVersion":"a","apiVersion":"b"}\n',
        "nonfinite.json": b'{"value":NaN}\n',
        "deep.json": _canonical_json(nested),
        "secret.json": _canonical_json(secret_document),
        "oversized.json": b" " * (MAX_FILE_BYTES + 1),
    }
    for name, payload in rejected.items():
        with pytest.raises(InputFailure):
            load_compiled_bundle(_write_raw(tmp_path / name, payload))

    result = _run_diff_cli(str(baseline), str(tmp_path / "secret.json"))
    assert result.returncode == 2
    assert result.stderr == "E_INPUT: unable to compare compiled bundles\n"
    assert secret not in result.stdout
    assert secret not in result.stderr


def test_diff_rejects_identity_and_api_version_mismatch(
    anatomical_example_root: Path,
    example_root: Path,
    tmp_path: Path,
) -> None:
    baseline_doc: dict[str, Any] = _compiled_document(anatomical_example_root)
    baseline = _artifact(tmp_path, "baseline.json", baseline_doc)

    identity_drift = copy.deepcopy(baseline_doc)
    identity_drift["metadata"]["architectureId"] = "bra-drift-identity"
    candidate = _artifact(tmp_path, "identity.json", identity_drift)
    identity_report = compare_compiled_bundles(baseline, candidate)
    assert not identity_report.allowed
    assert {finding.code for finding in identity_report.findings} == {"E_CHANGE_IDENTITY_MISMATCH"}

    api_version_drift = _compiled_document(example_root)
    api_version_candidate = _artifact(tmp_path, "api-version.json", api_version_drift)
    api_report = compare_compiled_bundles(baseline, api_version_candidate)
    assert not api_report.allowed
    assert {finding.code for finding in api_report.findings} == {"E_CHANGE_API_VERSION_MISMATCH"}


def test_diff_rejects_brainstem_mutation(anatomical_example_root: Path, tmp_path: Path) -> None:
    baseline_doc: dict[str, Any] = _compiled_document(anatomical_example_root)
    baseline = _artifact(tmp_path, "baseline.json", baseline_doc)

    candidate_doc: dict[str, Any] = copy.deepcopy(baseline_doc)
    brainstem = _find_by_component(candidate_doc["layers"], "spec.layer", "brainstem")
    brainstem["metadata"]["version"] = _bump_patch(str(brainstem["metadata"]["version"]))
    candidate = _artifact(tmp_path, "brainstem.json", candidate_doc)

    report = compare_compiled_bundles(baseline, candidate)
    assert not report.allowed
    assert any(finding.code == "E_CHANGE_BRAINSTEM" for finding in report.findings)


def test_diff_allows_controlled_layer_semantic_change(anatomical_example_root: Path, tmp_path: Path) -> None:
    baseline_doc: dict[str, Any] = _compiled_document(anatomical_example_root)
    baseline = _artifact(tmp_path, "baseline.json", baseline_doc)

    candidate_doc: dict[str, Any] = copy.deepcopy(baseline_doc)
    layer = _find_by_component(candidate_doc["layers"], "spec.layer", "cerebral-cortex")
    layer["spec"]["responsibilities"] = [*layer["spec"]["responsibilities"], "semantic-update-probe"]
    layer["metadata"]["version"] = _bump_patch(str(layer["metadata"]["version"]))
    layer["spec"]["changeControl"]["effectiveAt"] = "2099-01-01T00:00:00Z"
    candidate_doc["metadata"]["version"] = _bump_patch(str(candidate_doc["metadata"]["version"]))
    candidate = _artifact(tmp_path, "controlled.json", candidate_doc)

    report = compare_compiled_bundles(baseline, candidate)
    assert report.allowed
    assert any(finding.code == "OK_CONTROLLED_LAYER_UPDATE" for finding in report.findings)


def test_diff_rejects_missing_control_advances_and_empty_updates(
    anatomical_example_root: Path,
    tmp_path: Path,
) -> None:
    baseline_doc = _compiled_document(anatomical_example_root)
    baseline = _artifact(tmp_path, "baseline.json", baseline_doc)

    def candidate_document() -> tuple[dict[str, Any], dict[str, Any]]:
        document = copy.deepcopy(baseline_doc)
        layer = _find_by_component(document["layers"], "spec.layer", "cerebral-cortex")
        layer["spec"]["responsibilities"] = [*layer["spec"]["responsibilities"], "control-gate-probe"]
        return document, layer

    missing_layer_version, layer = candidate_document()
    layer["spec"]["changeControl"]["effectiveAt"] = "2099-01-01T00:00:00Z"
    missing_layer_version["metadata"]["version"] = _bump_patch(str(baseline_doc["metadata"]["version"]))
    report = compare_compiled_bundles(
        baseline,
        _artifact(tmp_path, "missing-layer-version.json", missing_layer_version),
    )
    assert any(finding.code == "E_CHANGE_LAYER_VERSION_NOT_ADVANCED" for finding in report.findings)

    missing_effective_at, layer = candidate_document()
    layer["metadata"]["version"] = _bump_patch(str(layer["metadata"]["version"]))
    missing_effective_at["metadata"]["version"] = _bump_patch(str(baseline_doc["metadata"]["version"]))
    report = compare_compiled_bundles(
        baseline,
        _artifact(tmp_path, "missing-effective-at.json", missing_effective_at),
    )
    assert any(finding.code == "E_CHANGE_EFFECTIVE_AT_NOT_ADVANCED" for finding in report.findings)

    missing_architecture_version, layer = candidate_document()
    layer["metadata"]["version"] = _bump_patch(str(layer["metadata"]["version"]))
    layer["spec"]["changeControl"]["effectiveAt"] = "2099-01-01T00:00:00Z"
    report = compare_compiled_bundles(
        baseline,
        _artifact(tmp_path, "missing-architecture-version.json", missing_architecture_version),
    )
    assert any(finding.code == "E_CHANGE_VERSION_NOT_ADVANCED" for finding in report.findings)

    empty_update = copy.deepcopy(baseline_doc)
    layer = _find_by_component(empty_update["layers"], "spec.layer", "cerebral-cortex")
    layer["metadata"]["version"] = _bump_patch(str(layer["metadata"]["version"]))
    layer["spec"]["changeControl"]["effectiveAt"] = "2099-01-01T00:00:00Z"
    report = compare_compiled_bundles(baseline, _artifact(tmp_path, "empty-update.json", empty_update))
    assert any(finding.code == "E_CHANGE_EMPTY_CONTROL_UPDATE" for finding in report.findings)


def test_diff_rejects_unsupported_component_changes(anatomical_example_root: Path, tmp_path: Path) -> None:
    baseline_doc: dict[str, Any] = _compiled_document(anatomical_example_root)
    baseline = _artifact(tmp_path, "baseline.json", baseline_doc)

    role_drift: dict[str, Any] = copy.deepcopy(baseline_doc)
    role_drift["roles"][0]["metadata"]["version"] = _bump_patch(str(role_drift["roles"][0]["metadata"]["version"]))
    role_candidate = _artifact(tmp_path, "role.json", role_drift)
    role_report = compare_compiled_bundles(baseline, role_candidate)
    assert not role_report.allowed
    assert any(finding.code == "E_CHANGE_CONTROL_UNAVAILABLE_ROLE" for finding in role_report.findings)

    policy_drift: dict[str, Any] = copy.deepcopy(baseline_doc)
    policy_drift["policies"][0]["metadata"]["version"] = _bump_patch(
        str(policy_drift["policies"][0]["metadata"]["version"])
    )
    policy_candidate = _artifact(tmp_path, "policy.json", policy_drift)
    policy_report = compare_compiled_bundles(baseline, policy_candidate)
    assert not policy_report.allowed
    assert any(finding.code == "E_CHANGE_CONTROL_UNAVAILABLE_POLICY" for finding in policy_report.findings)

    order_drift: dict[str, Any] = copy.deepcopy(baseline_doc)
    order_drift["compileOrder"] = [
        "brainstem",
        "hippocampus",
        "cerebellum",
        "amygdala",
        "cerebral-cortex",
        "prefrontal-cortex",
        "default-mode-network",
    ]
    layer_by_name = {str(layer["spec"]["layer"]): layer for layer in order_drift["layers"]}
    order_drift["layers"] = [layer_by_name[name] for name in order_drift["compileOrder"]]
    order_candidate = _artifact(tmp_path, "order.json", order_drift)
    order_report = compare_compiled_bundles(baseline, order_candidate)
    assert not order_report.allowed
    assert any(finding.code == "E_CHANGE_CONTROL_UNAVAILABLE_COMPILE_ORDER" for finding in order_report.findings)


def test_diff_report_is_deterministic_and_path_safe(anatomical_example_root: Path, tmp_path: Path) -> None:
    baseline_doc: dict[str, Any] = _compiled_document(anatomical_example_root)
    baseline = _artifact(tmp_path, "private-looking/baseline.json", baseline_doc)

    candidate_doc: dict[str, Any] = copy.deepcopy(baseline_doc)
    layer = _find_by_component(candidate_doc["layers"], "spec.layer", "cerebral-cortex")
    layer["spec"]["responsibilities"] = [*layer["spec"]["responsibilities"], "determinism-probe"]
    layer["metadata"]["version"] = _bump_patch(str(layer["metadata"]["version"]))
    layer["spec"]["changeControl"]["effectiveAt"] = "2099-01-01T00:00:00Z"
    candidate_doc["metadata"]["version"] = _bump_patch(str(candidate_doc["metadata"]["version"]))
    candidate = _artifact(tmp_path, "private-looking/candidate.json", candidate_doc)

    first = _run_diff_cli(str(baseline.path), str(candidate.path), "--format", "json")
    second = _run_diff_cli(str(baseline.path), str(candidate.path), "--format", "json")
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr == ""
    assert "private-looking" not in first.stdout
    assert "private-looking" not in first.stderr
    payload = json.loads(first.stdout)
    assert payload["allowed"] is True
    assert payload["kind"] == "ChangeReport"
    assert validate_document(payload, "change-report.json") == []

    text_first = _run_diff_cli(str(baseline.path), str(candidate.path), "--format", "text")
    text_second = _run_diff_cli(str(baseline.path), str(candidate.path), "--format", "text")
    assert text_first.returncode == text_second.returncode == 0
    assert text_first.stdout == text_second.stdout
    assert "private-looking" not in text_first.stdout

    direct_report = compare_compiled_bundles(baseline, candidate)
    assert json.loads(json_report(direct_report)) == payload
