from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from brain_role.adapters import hermes
from brain_role.errors import InputFailure


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "brain_role", *args], text=True, capture_output=True, check=False)


def test_hermes_export_is_deterministic_and_prefill_compatible(example_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "export"
    first = run_cli("render", "hermes", str(example_root), "--output", str(output))
    first_bytes = (output / "prefill_messages.json").read_bytes()
    second = run_cli("render", "hermes", str(example_root), "--output", str(output))
    second_bytes = (output / "prefill_messages.json").read_bytes()
    assert first.returncode == second.returncode == 0
    assert first_bytes == second_bytes
    payload = json.loads(first_bytes)
    assert isinstance(payload, list) and payload[0]["role"] == "system"
    assert hashlib.sha256(first_bytes).hexdigest() in first.stdout
    assert "~/.hermes" not in first_bytes.decode()


def test_invalid_instance_writes_nothing(instance_copy: Path, tmp_path: Path) -> None:
    (instance_copy / "layers" / "p0.yaml").unlink()
    output = tmp_path / "export"
    result = run_cli("render", "hermes", str(instance_copy), "--output", str(output))
    assert result.returncode == 1
    assert not output.exists()


def test_runtime_home_output_is_rejected(monkeypatch: object, example_root: Path, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(hermes.Path, "home", classmethod(lambda cls: fake_home))  # type: ignore[attr-defined]
    from brain_role.validator import validate_instance

    result = validate_instance(example_root)
    assert result.bundle is not None and result.valid
    try:
        hermes.render_prefill(result.bundle, fake_home / ".hermes" / "generated")
    except InputFailure:
        pass
    else:
        raise AssertionError("runtime home output must be rejected")
