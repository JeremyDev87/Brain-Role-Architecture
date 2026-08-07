from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from conftest import load_yaml, save_yaml

from brain_role.compiler import compile_bundle, write_compiled_bundle
from brain_role.validator import validate_instance


def run_cli(
    *args: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "brain_role", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _compiled_bundle(anatomical_example_root: Path) -> dict[str, Any]:
    validated = validate_instance(anatomical_example_root)
    assert validated.valid and validated.bundle is not None
    return compile_bundle(validated.bundle)


def _write_compiled(tmp_path: Path, name: str, document: dict[str, Any]) -> Path:
    target = tmp_path / name
    write_compiled_bundle(document, target)
    return target


def _bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def test_cli_valid_json_is_byte_deterministic(example_root: Path) -> None:
    first = run_cli("validate", str(example_root), "--format", "json")
    second = run_cli("validate", str(example_root), "--format", "json")
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr == ""
    assert json.loads(first.stdout) == {
        "errors": [],
        "specVersion": "0.1.0",
        "valid": True,
    }


def test_cli_conformance_failure_is_exit_one(instance_copy: Path) -> None:
    (instance_copy / "layers" / "p0.yaml").unlink()
    result = run_cli("validate", str(instance_copy))
    assert result.returncode == 1
    assert "E_REF_MISSING" in result.stdout


def test_cli_input_failure_is_exit_two_without_path_echo(tmp_path: Path) -> None:
    missing = tmp_path / "private-looking-name" / "missing"
    result = run_cli("validate", str(missing))
    assert result.returncode == 2
    assert str(tmp_path) not in result.stderr
    assert result.stderr == "E_INPUT: unable to load input\n"


def test_cli_schema_failures_never_echo_input_secrets(instance_copy: Path) -> None:
    secret = "ghp_" + "A" * 24
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["metadata"]["id"] = secret
    save_yaml(target, document)
    for output_format in ("text", "json"):
        result = run_cli(
            "validate",
            str(instance_copy),
            "--format",
            output_format,
        )
        assert result.returncode == 1
        assert secret not in result.stdout
        assert secret not in result.stderr
        assert "E_SCHEMA" in result.stdout
        assert "E_PUBLIC_BOUNDARY" in result.stdout


def test_cli_does_not_echo_secret_reference(instance_copy: Path) -> None:
    secret = "ghp_" + "A" * 24
    architecture = instance_copy / "architecture.yaml"
    document = load_yaml(architecture)
    document["layers"][0] = secret + ".yaml"
    save_yaml(architecture, document)
    for output_format in ("text", "json"):
        result = run_cli("validate", str(instance_copy), "--format", output_format)
        assert result.returncode == 1
        assert secret not in result.stdout
        assert secret not in result.stderr
        assert "E_REF_MISSING" in result.stdout
        assert "E_PUBLIC_BOUNDARY" in result.stdout


def test_cli_does_not_echo_secret_pointer_key(instance_copy: Path) -> None:
    secret = "ghp_" + "A" * 24
    target = instance_copy / "roles" / "operator.yaml"
    document = load_yaml(target)
    document["spec"][secret + "_token"] = "synthetic-secret-value-123"
    save_yaml(target, document)
    for output_format in ("text", "json"):
        result = run_cli("validate", str(instance_copy), "--format", output_format)
        assert result.returncode == 1
        assert secret not in result.stdout
        assert secret not in result.stderr
        assert "E_SCHEMA" in result.stdout
        assert "E_SECRET_LITERAL" in result.stdout


def test_cli_version() -> None:
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout == "brain-role 0.4.0\n"


def test_cli_diff_exit_codes_are_0_1_2(anatomical_example_root: Path, tmp_path: Path) -> None:
    baseline_doc: dict[str, Any] = _compiled_bundle(anatomical_example_root)
    baseline = _write_compiled(tmp_path, "baseline.json", baseline_doc)

    allowed_doc: dict[str, Any] = copy.deepcopy(baseline_doc)
    controlled_layer = next(layer for layer in allowed_doc["layers"] if layer["spec"]["layer"] == "cerebral-cortex")
    controlled_layer["spec"]["responsibilities"] = [
        *controlled_layer["spec"]["responsibilities"],
        "cli-probe",
    ]
    controlled_layer["metadata"]["version"] = _bump_patch(str(controlled_layer["metadata"]["version"]))
    controlled_layer["spec"]["changeControl"]["effectiveAt"] = "2099-01-01T00:00:00Z"
    allowed_doc["metadata"]["version"] = _bump_patch(str(allowed_doc["metadata"]["version"]))
    allowed = _write_compiled(tmp_path, "allowed.json", allowed_doc)
    allowed_result = run_cli("diff", str(baseline), str(allowed), "--format", "json")
    assert allowed_result.returncode == 0
    assert json.loads(allowed_result.stdout)["allowed"] is True

    denied_doc: dict[str, Any] = copy.deepcopy(baseline_doc)
    denied_doc["roles"][0]["metadata"]["version"] = _bump_patch(
        str(denied_doc["roles"][0]["metadata"]["version"])
    )
    denied = _write_compiled(tmp_path, "denied.json", denied_doc)
    denied_result = run_cli("diff", str(baseline), str(denied))
    assert denied_result.returncode == 1
    assert "E_CHANGE_CONTROL_UNAVAILABLE_ROLE" in denied_result.stdout

    missing = tmp_path / "missing.json"
    missing_result = run_cli("diff", str(baseline), str(missing))
    assert missing_result.returncode == 2
    assert missing_result.stderr == "E_INPUT: unable to compare compiled bundles\n"
