from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import load_yaml, save_yaml


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
