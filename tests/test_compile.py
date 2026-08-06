from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from conftest import load_yaml, save_yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from brain_role.errors import InputFailure
from brain_role.schema_validation import load_schema
from brain_role.validator import validate_instance

ROOT = Path(__file__).resolve().parents[1]


def compiler_module() -> ModuleType:
    return importlib.import_module("brain_role.compiler")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "brain_role", *args], text=True, capture_output=True, check=False)


def compiled_validator() -> Draft202012Validator:
    names = ("compiled-bundle", "layer", "role", "policy")
    schemas = [load_schema(f"{name}.schema.json") for name in names]
    resources = [(str(schema["$id"]), Resource.from_contents(schema)) for schema in schemas]
    return Draft202012Validator(schemas[0], registry=Registry().with_resources(resources))


def compile_example(example_root: Path) -> tuple[Any, dict[str, Any]]:
    result = validate_instance(example_root)
    assert result.valid and result.bundle is not None
    module = compiler_module()
    return module, module.compile_bundle(result.bundle)


def test_compiled_bundle_has_minimal_schema_and_deterministic_order(example_root: Path) -> None:
    module, document = compile_example(example_root)
    assert set(document) == {"apiVersion", "kind", "metadata", "compileOrder", "layers", "roles", "policies"}
    assert document["apiVersion"] == "brain-role.dev/v1alpha1"
    assert document["kind"] == "CompiledBrainRole"
    assert document["compileOrder"] == ["P0", "P1", "P2", "P3", "P4", "P6", "P5"]
    assert [layer["spec"]["layer"] for layer in document["layers"]] == document["compileOrder"]
    assert [role["metadata"]["id"] for role in document["roles"]] == [
        "synthetic-observer",
        "synthetic-operator",
    ]
    assert [policy["metadata"]["id"] for policy in document["policies"]] == ["p0-protection"]
    compiled_validator().validate(document)

    first = module.encode_compiled_bundle(document)
    second = module.encode_compiled_bundle(document)
    assert first == second
    assert first.endswith(b"\n")
    assert first == (json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
    assert str(example_root).encode() not in first
    assert b"runtimeActivation" not in first


def test_compiled_schema_rejects_unknown_top_level_field(example_root: Path) -> None:
    _, document = compile_example(example_root)
    document["sourcePath"] = "/synthetic/private/path"
    errors = list(compiled_validator().iter_errors(document))
    assert errors


def test_compiled_schema_and_semantic_validator_reject_inconsistent_layers(example_root: Path) -> None:
    module, document = compile_example(example_root)
    duplicate = json.loads(json.dumps(document))
    duplicate["layers"][1] = duplicate["layers"][0]
    assert list(compiled_validator().iter_errors(duplicate))

    reversed_layers = json.loads(json.dumps(document))
    reversed_layers["layers"] = list(reversed(reversed_layers["layers"]))
    with pytest.raises(InputFailure):
        module.validate_compiled_bundle(reversed_layers)

    valid_alternative_order = ["P0", "P2", "P1", "P3", "P4", "P6", "P5"]
    valid_alternative = json.loads(json.dumps(document))
    layers_by_name = {layer["spec"]["layer"]: layer for layer in valid_alternative["layers"]}
    valid_alternative["compileOrder"] = valid_alternative_order
    valid_alternative["layers"] = [layers_by_name[layer] for layer in valid_alternative_order]
    module.validate_compiled_bundle(valid_alternative)

    dependency_violation_order = ["P0", "P5", "P1", "P2", "P3", "P4", "P6"]
    dependency_violation = json.loads(json.dumps(document))
    layers_by_name = {layer["spec"]["layer"]: layer for layer in dependency_violation["layers"]}
    dependency_violation["compileOrder"] = dependency_violation_order
    dependency_violation["layers"] = [layers_by_name[layer] for layer in dependency_violation_order]
    with pytest.raises(InputFailure):
        module.validate_compiled_bundle(dependency_violation)

    duplicate_order = json.loads(json.dumps(document))
    duplicate_order["compileOrder"][-1] = "P0"
    duplicate_order["layers"][-1] = duplicate_order["layers"][0]
    with pytest.raises(InputFailure):
        module.validate_compiled_bundle(duplicate_order)

    duplicate_role_id = json.loads(json.dumps(document))
    duplicate_role_id["roles"][1]["metadata"]["id"] = duplicate_role_id["roles"][0]["metadata"]["id"]
    with pytest.raises(InputFailure):
        module.validate_compiled_bundle(duplicate_role_id)

    duplicate_policy_id = json.loads(json.dumps(document))
    second_policy = json.loads(json.dumps(duplicate_policy_id["policies"][0]))
    second_policy["spec"]["denySelfEscalation"] = False
    duplicate_policy_id["policies"].append(second_policy)
    with pytest.raises(InputFailure):
        module.validate_compiled_bundle(duplicate_policy_id)


def test_compile_cli_is_byte_deterministic_and_reports_sha(example_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "compiled.json"
    first = run_cli("compile", str(example_root), "--output", str(output))
    first_bytes = output.read_bytes()
    second = run_cli("compile", str(example_root), "--output", str(output))
    second_bytes = output.read_bytes()
    digest = hashlib.sha256(first_bytes).hexdigest()
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout == f"COMPILED file=compiled.json sha256={digest}\n"
    assert first.stderr == second.stderr == ""
    assert first_bytes == second_bytes
    compiled_validator().validate(json.loads(first_bytes))


def test_compile_rejects_control_character_receipt_injection(example_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "receipt\nFORGED status=ok.json"
    result = run_cli("compile", str(example_root), "--output", str(output))
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "E_OUTPUT: unable to write compiled output\n"
    assert not output.exists()


def test_invalid_compile_preserves_existing_output(instance_copy: Path, tmp_path: Path) -> None:
    (instance_copy / "layers" / "p0.yaml").unlink()
    output = tmp_path / "compiled.json"
    output.write_bytes(b"preserve-existing-output\n")
    result = run_cli("compile", str(instance_copy), "--output", str(output))
    assert result.returncode == 1
    assert "E_REF_MISSING" in result.stdout
    assert result.stderr == ""
    assert output.read_bytes() == b"preserve-existing-output\n"


def test_safe_output_path_rejects_first_path_component_symlink() -> None:
    if not Path("/tmp").is_symlink():
        pytest.skip("this platform has no /tmp symlink to exercise")
    output_safety = importlib.import_module("brain_role.output_safety")
    with pytest.raises(InputFailure, match="symlink"):
        output_safety.safe_output_path(Path("/tmp") / "compiled.json")


def test_compile_rejects_native_and_symlink_outputs(
    example_root: Path,
    tmp_path: Path,
) -> None:
    module, document = compile_example(example_root)

    for target in (
        tmp_path / "MEMORY.md",
        tmp_path / "memory.md",
    ):
        with pytest.raises(InputFailure):
            module.write_compiled_bundle(document, target)
        assert not target.exists()

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(InputFailure):
        module.write_compiled_bundle(document, linked_parent / "compiled.json")
    assert list(real_parent.iterdir()) == []

    real_file = tmp_path / "real-file.json"
    real_file.write_bytes(b"preserve-symlink-target\n")
    linked_file = tmp_path / "linked-file.json"
    linked_file.symlink_to(real_file)
    with pytest.raises(InputFailure):
        module.write_compiled_bundle(document, linked_file)
    assert real_file.read_bytes() == b"preserve-symlink-target\n"


def test_compile_is_independent_of_source_reference_order(instance_copy: Path, example_root: Path) -> None:
    module, original = compile_example(example_root)
    architecture_path = instance_copy / "architecture.yaml"
    architecture = load_yaml(architecture_path)
    architecture["layers"] = list(reversed(architecture["layers"]))
    architecture["roles"] = list(reversed(architecture["roles"]))
    save_yaml(architecture_path, architecture)
    result = validate_instance(instance_copy)
    assert result.valid and result.bundle is not None
    reordered = module.compile_bundle(result.bundle)
    assert module.encode_compiled_bundle(reordered) == module.encode_compiled_bundle(original)


def test_atomic_replace_failure_preserves_existing_output(
    monkeypatch: pytest.MonkeyPatch,
    example_root: Path,
    tmp_path: Path,
) -> None:
    module, document = compile_example(example_root)
    output_safety = importlib.import_module("brain_role.output_safety")
    output = tmp_path / "compiled.json"
    output.write_bytes(b"preserve-on-replace-failure\n")

    def fail_replace(*args: Any, **kwargs: Any) -> None:
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(output_safety.os, "replace", fail_replace)
    with pytest.raises(InputFailure):
        module.write_compiled_bundle(document, output)
    assert output.read_bytes() == b"preserve-on-replace-failure\n"
    assert list(tmp_path.glob(".compiled.json.*.tmp")) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory-fd race probe")
def test_parent_swap_before_directory_pin_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    example_root: Path,
    tmp_path: Path,
) -> None:
    module, document = compile_example(example_root)
    output_safety = importlib.import_module("brain_role.output_safety")
    checked_parent = tmp_path / "checked-parent"
    checked_parent.mkdir()
    moved_parent = tmp_path / "moved-parent"
    evil_parent = tmp_path / "evil-parent"
    evil_parent.mkdir()
    real_open = output_safety.os.open
    swapped = False

    def swap_then_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        nonlocal swapped
        if not swapped and kwargs.get("dir_fd") is None and Path(path) == checked_parent:
            checked_parent.rename(moved_parent)
            checked_parent.symlink_to(evil_parent, target_is_directory=True)
            swapped = True
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(output_safety.os, "open", swap_then_open)
    with pytest.raises(InputFailure):
        module.write_compiled_bundle(document, checked_parent / "compiled.json")
    assert swapped
    assert list(evil_parent.iterdir()) == []
    assert list(moved_parent.iterdir()) == []
